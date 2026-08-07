from dataclasses import dataclass
from datetime import date, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models.feriado import Feriado
from app.database.models.regla_hora import ReglaHora
from app.database.models.usuario import Usuario


DOS_DECIMALES = Decimal("0.01")
MINUTOS_POR_HORA = Decimal("60")
MINUTOS_POR_DIA = 24 * 60


class CalculoHorasError(ValueError):
    """Error de negocio que impide calcular una solicitud de horas extras."""


@dataclass(frozen=True)
class ResultadoHorasExtra:
    usuario_id: int
    usuario_nombre: str
    legajo: str | None
    convenio: str
    fecha: date
    hora_inicio: time | None
    hora_fin: time | None
    tipo_dia: str
    tipo_hora: str | None
    horas_totales: Decimal | None
    horas_nocturnas: Decimal | None
    permite_reintegro: bool
    regla_id: int
    tipo_registro: str = "HORAS"


def _hora_a_minutos(valor: time) -> int:
    return valor.hour * 60 + valor.minute


def _minutos_a_horas(minutos: int) -> Decimal:
    return (Decimal(minutos) / MINUTOS_POR_HORA).quantize(
        DOS_DECIMALES,
        rounding=ROUND_HALF_UP,
    )


def clasificar_tipo_dia(fecha: date, db: Session) -> str:
    existe_feriado = db.scalar(
        select(Feriado.id).where(Feriado.fecha == fecha).limit(1)
    )
    if existe_feriado is not None:
        return "FERIADO"
    return "HABIL"


def calcular_horas_totales(hora_inicio: time, hora_fin: time) -> Decimal:
    minutos_inicio = _hora_a_minutos(hora_inicio)
    minutos_fin = _hora_a_minutos(hora_fin)
    # Un tramo generado al dividir una carga en medianoche se representa como
    # HH:MM -> 00:00 dentro de la fecha en la que comenzó.
    if minutos_fin == 0 and minutos_inicio > 0:
        minutos_fin = MINUTOS_POR_DIA
    if minutos_fin <= minutos_inicio:
        raise CalculoHorasError(
            "La hora de finalización debe ser distinta de la hora de inicio."
        )
    return _minutos_a_horas(minutos_fin - minutos_inicio)


def dividir_carga_en_fechas(
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
) -> list[tuple[date, time, time]]:
    """Divide en medianoche una carga que finaliza al día siguiente."""
    minutos_inicio = _hora_a_minutos(hora_inicio)
    minutos_fin = _hora_a_minutos(hora_fin)

    if minutos_inicio == minutos_fin:
        raise CalculoHorasError(
            "La hora de finalización debe ser distinta de la hora de inicio."
        )
    if minutos_fin == 0 or minutos_fin > minutos_inicio:
        return [(fecha, hora_inicio, hora_fin)]
    return [
        (fecha, hora_inicio, time(0, 0)),
        (fecha + timedelta(days=1), time(0, 0), hora_fin),
    ]


def _minutos_superpuestos(
    inicio: int,
    fin: int,
    intervalo_inicio: int,
    intervalo_fin: int,
) -> int:
    return max(0, min(fin, intervalo_fin) - max(inicio, intervalo_inicio))


def calcular_horas_nocturnas(
    hora_inicio: time,
    hora_fin: time,
    nocturna_desde: time | None,
    nocturna_hasta: time | None,
) -> Decimal:
    calcular_horas_totales(hora_inicio, hora_fin)
    if nocturna_desde is None or nocturna_hasta is None:
        return Decimal("0.00")

    inicio = _hora_a_minutos(hora_inicio)
    fin = _hora_a_minutos(hora_fin)
    if fin == 0 and inicio > 0:
        fin = MINUTOS_POR_DIA
    desde = _hora_a_minutos(nocturna_desde)
    hasta = _hora_a_minutos(nocturna_hasta)

    if desde == hasta:
        minutos_nocturnos = fin - inicio
    elif desde < hasta:
        minutos_nocturnos = _minutos_superpuestos(inicio, fin, desde, hasta)
    else:
        minutos_nocturnos = (
            _minutos_superpuestos(inicio, fin, 0, hasta)
            + _minutos_superpuestos(inicio, fin, desde, MINUTOS_POR_DIA)
        )
    return _minutos_a_horas(minutos_nocturnos)


def obtener_regla_horas(
    convenio: str,
    tipo_dia: str,
    db: Session,
) -> ReglaHora:
    convenio_normalizado = convenio.strip().upper()
    tipo_dia_normalizado = tipo_dia.strip().upper()
    reglas = list(db.scalars(
        select(ReglaHora)
        .where(
            func.upper(ReglaHora.convenio) == convenio_normalizado,
            func.upper(ReglaHora.tipo_dia) == tipo_dia_normalizado,
        )
        .order_by(ReglaHora.id)
        .limit(2)
    ))
    if not reglas:
        raise CalculoHorasError(
            f"No existe una regla de horas para el convenio {convenio_normalizado} y el tipo de día {tipo_dia_normalizado}."
        )
    if len(reglas) > 1:
        raise CalculoHorasError(
            f"Hay más de una regla para el convenio {convenio_normalizado} y el tipo de día {tipo_dia_normalizado}. Revisá la configuración."
        )
    return reglas[0]


def calcular_resultado_horas_extra(
    usuario_id: int,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    db: Session,
    marcar_como_franco: bool = False,
) -> ResultadoHorasExtra:
    if fecha is None or hora_inicio is None or hora_fin is None:
        raise CalculoHorasError("La fecha, la hora de inicio y la hora de finalización son obligatorias.")
    if (
        hora_inicio.minute not in {0, 30}
        or hora_fin.minute not in {0, 30}
        or hora_inicio.second != 0
        or hora_fin.second != 0
    ):
        raise CalculoHorasError("Las horas de inicio y finalización deben ingresarse cada 30 minutos.")

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise CalculoHorasError("El usuario seleccionado no existe.")
    if not usuario.status:
        raise CalculoHorasError("El usuario seleccionado está inactivo.")
    if not usuario.convenio:
        raise CalculoHorasError("El usuario no tiene un convenio asignado.")

    horas_totales = calcular_horas_totales(hora_inicio, hora_fin)
    tipo_dia = "FRANCO" if marcar_como_franco else clasificar_tipo_dia(fecha, db)
    regla = obtener_regla_horas(usuario.convenio, tipo_dia, db)
    horas_nocturnas = calcular_horas_nocturnas(
        hora_inicio,
        hora_fin,
        regla.hora_nocturna_desde,
        regla.hora_nocturna_hasta,
    )

    return ResultadoHorasExtra(
        usuario_id=usuario.id,
        usuario_nombre=f"{usuario.apellido}, {usuario.nombre}",
        legajo=usuario.legajo,
        convenio=usuario.convenio,
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        tipo_dia=tipo_dia,
        tipo_hora=regla.tipo_hora,
        horas_totales=horas_totales,
        horas_nocturnas=horas_nocturnas,
        permite_reintegro=regla.permite_reintegro,
        regla_id=regla.id,
    )


def calcular_resultado_reintegro(
    usuario_id: int,
    fecha: date,
    db: Session,
) -> ResultadoHorasExtra:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise CalculoHorasError("El usuario seleccionado no existe.")
    if not usuario.status:
        raise CalculoHorasError("El usuario seleccionado está inactivo.")
    if not usuario.convenio:
        raise CalculoHorasError("El usuario no tiene un convenio asignado.")

    tipo_dia = clasificar_tipo_dia(fecha, db)
    if tipo_dia != "FERIADO":
        tipo_dia = "FRANCO"
    regla = obtener_regla_horas(usuario.convenio, tipo_dia, db)
    if not regla.permite_reintegro:
        raise CalculoHorasError("La regla correspondiente a ese día no permite solicitar reintegro.")

    return ResultadoHorasExtra(
        usuario_id=usuario.id,
        usuario_nombre=f"{usuario.apellido}, {usuario.nombre}",
        legajo=usuario.legajo,
        convenio=usuario.convenio,
        fecha=fecha,
        hora_inicio=None,
        hora_fin=None,
        tipo_dia=tipo_dia,
        tipo_hora=None,
        horas_totales=None,
        horas_nocturnas=None,
        permite_reintegro=True,
        regla_id=regla.id,
        tipo_registro="REINTEGRO",
    )
