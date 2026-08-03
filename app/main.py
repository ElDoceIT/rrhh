from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated
from urllib.parse import quote, unquote

import bcrypt
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.database.connection import engine, get_db
from app.database.models import Feriado, HoraExtra, ReglaHora, TipoContratacion, Usuario, UsuarioRol
from app.services.calculo_horas import CalculoHorasError, calcular_resultado_horas_extra

app = FastAPI(title="Horas extras")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def parse_optional_time(value: str | None) -> time | None:
    if not value:
        return None
    try:
        return time.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="El horario ingresado no es válido.") from error


def rule_form_data(
    convenio: str,
    tipo_dia: str,
    tipo_hora: str,
    hora_nocturna_desde: str | None,
    hora_nocturna_hasta: str | None,
    permite_reintegro: str | None,
    observaciones: str | None,
) -> dict:
    convenio = convenio.strip()
    tipo_dia = tipo_dia.strip()
    tipo_hora = tipo_hora.strip()
    if not convenio or not tipo_dia or not tipo_hora:
        raise HTTPException(status_code=422, detail="Completá los campos obligatorios.")
    return {
        "convenio": convenio,
        "tipo_dia": tipo_dia,
        "tipo_hora": tipo_hora,
        "hora_nocturna_desde": parse_optional_time(hora_nocturna_desde),
        "hora_nocturna_hasta": parse_optional_time(hora_nocturna_hasta),
        "permite_reintegro": permite_reintegro == "on",
        "observaciones": observaciones.strip() if observaciones else None,
    }


def clean_optional(value: str | None) -> str | None:
    value = value.strip() if value else ""
    return value or None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def encode_carga(
    usuario_id: int,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    observaciones: str | None,
) -> str:
    return "|".join((
        str(usuario_id),
        fecha.isoformat(),
        hora_inicio.strftime("%H:%M"),
        hora_fin.strftime("%H:%M"),
        quote(clean_optional(observaciones) or "", safe=""),
    ))


def decode_carga(value: str) -> tuple[int, date, time, time, str | None]:
    try:
        usuario_id, fecha, hora_inicio, hora_fin, observaciones = value.split("|", maxsplit=4)
        return (
            int(usuario_id),
            date.fromisoformat(fecha),
            time.fromisoformat(hora_inicio),
            time.fromisoformat(hora_fin),
            clean_optional(unquote(observaciones)),
        )
    except (TypeError, ValueError) as error:
        raise CalculoHorasError("La solicitud contiene una carga con formato inválido.") from error


def periodo_corte(fecha_referencia: date) -> tuple[date, date]:
    corte_actual = date(fecha_referencia.year, fecha_referencia.month, 20)
    if fecha_referencia.day > 20:
        desde = corte_actual
        if fecha_referencia.month == 12:
            hasta = date(fecha_referencia.year + 1, 1, 20)
        else:
            hasta = date(fecha_referencia.year, fecha_referencia.month + 1, 20)
    else:
        hasta = corte_actual
        if fecha_referencia.month == 1:
            desde = date(fecha_referencia.year - 1, 12, 20)
        else:
            desde = date(fecha_referencia.year, fecha_referencia.month - 1, 20)
    return desde, hasta


def obtener_jefe(jefe_id: int, db: Session) -> Usuario:
    jefe = db.get(Usuario, jefe_id)
    if jefe is None or not jefe.status or jefe.perfil != "JEFE":
        raise HTTPException(
            status_code=403,
            detail="El usuario seleccionado no está habilitado como jefe.",
        )
    return jefe


def validar_hora_para_jefe(
    hora: HoraExtra | None,
    jefe: Usuario,
    requiere_pendiente: bool = True,
) -> HoraExtra:
    if hora is None:
        raise HTTPException(status_code=404, detail="La carga de horas no existe.")
    if hora.usuario.id_rol != jefe.id_rol:
        raise HTTPException(
            status_code=403,
            detail="No podés administrar horas de usuarios con otro rol.",
        )
    if requiere_pendiente and hora.estado != "PENDIENTE":
        raise HTTPException(
            status_code=409,
            detail="La carga ya no está pendiente de autorización.",
        )
    return hora


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    estado: str | None = None,
    usuario_id: int | None = None,
    guardado: int | None = None,
    db: Session = Depends(get_db),
):
    desde, hasta = periodo_corte(date.today())
    horas: list[HoraExtra] = []
    usuarios: list[Usuario] = []
    error = None
    try:
        usuarios = list(db.scalars(
            select(Usuario)
            .where(Usuario.status.is_(True))
            .order_by(Usuario.apellido, Usuario.nombre)
        ))
        consulta = (
            select(HoraExtra)
            .options(selectinload(HoraExtra.usuario), selectinload(HoraExtra.aprobador))
            .where(HoraExtra.fecha >= desde, HoraExtra.fecha <= hasta)
            .order_by(HoraExtra.fecha.desc(), HoraExtra.hora_inicio.desc())
        )
        if estado:
            consulta = consulta.where(HoraExtra.estado == estado)
        if usuario_id is not None:
            consulta = consulta.where(HoraExtra.usuario_id == usuario_id)
        horas = list(db.scalars(consulta))
    except SQLAlchemyError:
        error = "No se pudieron cargar las horas extras. Verificá la conexión con la base."
    return templates.TemplateResponse(request, "dashboard.html", {
        "active_page": "home",
        "horas": horas,
        "usuarios": usuarios,
        "desde": desde,
        "hasta": hasta,
        "estado_filtro": estado or "",
        "usuario_filtro": usuario_id,
        "guardado": guardado,
        "total_horas": sum(
            (hora.horas_totales for hora in horas),
            start=Decimal("0.00"),
        ),
        "cantidad_pendientes": sum(
            1 for hora in horas if hora.estado == "PENDIENTE"
        ),
        "cantidad_autorizadas": sum(
            1 for hora in horas if hora.estado == "APROBADA"
        ),
        "error": error,
    })


@app.get("/solicitudes/nueva", response_class=HTMLResponse)
def nueva_solicitud(request: Request, db: Session = Depends(get_db)):
    usuarios: list[Usuario] = []
    error = None
    try:
        usuarios = list(db.scalars(
            select(Usuario)
            .where(Usuario.status.is_(True))
            .order_by(Usuario.apellido, Usuario.nombre)
        ))
    except SQLAlchemyError:
        error = "No se pudieron cargar los usuarios activos. Verificá la conexión con la base."
    return templates.TemplateResponse(request, "home.html", {
        "active_page": "home",
        "usuarios": usuarios,
        "fecha_hoy": date.today().isoformat(),
        "error": error,
    })


@app.post("/solicitudes/procesar", response_class=HTMLResponse)
def procesar_solicitud(
    request: Request,
    usuario_id: Annotated[int, Form()],
    fecha: Annotated[date, Form()],
    hora_inicio: Annotated[time, Form()],
    hora_fin: Annotated[time, Form()],
    observaciones: Annotated[str | None, Form()] = None,
    cargas: Annotated[list[str] | None, Form()] = None,
    reintegros: Annotated[list[str] | None, Form()] = None,
    db: Session = Depends(get_db),
):
    resultados = []
    observaciones_resultados: list[str | None] = []
    cargas_codificadas = list(cargas or [])
    selecciones_reintegro = [
        value if value in {"SI", "NO"} else "NO"
        for value in (reintegros or [])
    ]
    if len(selecciones_reintegro) < len(cargas_codificadas):
        selecciones_reintegro.extend(
            ["NO"] * (len(cargas_codificadas) - len(selecciones_reintegro))
        )
    selecciones_reintegro = selecciones_reintegro[:len(cargas_codificadas)]
    error = None
    try:
        for carga in cargas_codificadas:
            datos = decode_carga(carga)
            resultados.append(calcular_resultado_horas_extra(*datos[:4], db))
            observaciones_resultados.append(datos[4])
        nuevo_resultado = calcular_resultado_horas_extra(
            usuario_id,
            fecha,
            hora_inicio,
            hora_fin,
            db,
        )
        resultados.append(nuevo_resultado)
        observaciones_resultados.append(clean_optional(observaciones))
        cargas_codificadas.append(encode_carga(
            usuario_id, fecha, hora_inicio, hora_fin, observaciones,
        ))
        selecciones_reintegro.append("NO")
    except CalculoHorasError as exc:
        error = str(exc)

    usuarios = list(db.scalars(
        select(Usuario)
        .where(Usuario.status.is_(True))
        .order_by(Usuario.apellido, Usuario.nombre)
    ))
    return templates.TemplateResponse(
        request,
        "solicitud.html",
        {
            "active_page": "home",
            "resultados": resultados,
            "observaciones_resultados": observaciones_resultados,
            "cargas": cargas_codificadas,
            "reintegros": selecciones_reintegro,
            "usuarios": usuarios,
            "fecha_hoy": date.today().isoformat(),
            "total_horas": sum((item.horas_totales for item in resultados), start=0),
            "total_nocturnas": sum((item.horas_nocturnas for item in resultados), start=0),
            "error": error,
        },
        status_code=422 if error and not resultados else 200,
    )


@app.post("/solicitudes/confirmar")
def confirmar_solicitud(
    cargas: Annotated[list[str], Form()],
    reintegros: Annotated[list[str] | None, Form()] = None,
    db: Session = Depends(get_db),
):
    if not cargas:
        raise HTTPException(status_code=422, detail="La solicitud no contiene cargas.")
    selecciones = list(reintegros or [])
    if len(selecciones) != len(cargas):
        raise HTTPException(status_code=422, detail="La selección de reintegros es inconsistente.")

    try:
        for indice, carga in enumerate(cargas):
            datos = decode_carga(carga)
            resultado = calcular_resultado_horas_extra(*datos[:4], db)
            solicita_reintegro = (
                resultado.permite_reintegro
                and selecciones[indice] == "SI"
            )
            db.add(HoraExtra(
                usuario_id=resultado.usuario_id,
                fecha=resultado.fecha,
                hora_inicio=resultado.hora_inicio,
                hora_fin=resultado.hora_fin,
                horas_totales=resultado.horas_totales,
                tipo_dia=resultado.tipo_dia,
                tipo_hora=resultado.tipo_hora,
                horas_nocturnas=resultado.horas_nocturnas,
                solicita_reintegro=solicita_reintegro,
                observaciones=datos[4],
                estado="PENDIENTE",
                aprobado_por=None,
                fecha_carga=datetime.now(),
            ))
        db.commit()
    except (CalculoHorasError, SQLAlchemyError) as error:
        db.rollback()
        mensaje = str(error) if isinstance(error, CalculoHorasError) else "No se pudo guardar la solicitud en la base de datos."
        raise HTTPException(status_code=422, detail=mensaje) from error
    return RedirectResponse(f"/?guardado={len(cargas)}", status_code=303)


@app.get("/configuracion/parametros", response_class=HTMLResponse)
def parametros(
    request: Request,
    editar: int | None = None,
    guardado: str | None = None,
    db: Session = Depends(get_db),
):
    error = None
    reglas: list[ReglaHora] = []
    regla_edicion = None
    try:
        reglas = list(db.scalars(select(ReglaHora).order_by(ReglaHora.convenio, ReglaHora.tipo_dia, ReglaHora.id)))
        if editar is not None:
            regla_edicion = db.get(ReglaHora, editar)
            if regla_edicion is None:
                error = "La regla seleccionada no existe."
    except SQLAlchemyError:
        error = "No se pudieron cargar las reglas. Verificá la conexión con la base de datos."

    return templates.TemplateResponse(
        request,
        "parametros.html",
        {
            "active_page": "parametros",
            "reglas": reglas,
            "regla_edicion": regla_edicion,
            "guardado": guardado,
            "error": error,
        },
    )


@app.post("/configuracion/parametros/reglas")
def crear_regla(
    convenio: Annotated[str, Form()],
    tipo_dia: Annotated[str, Form()],
    tipo_hora: Annotated[str, Form()],
    hora_nocturna_desde: Annotated[str | None, Form()] = None,
    hora_nocturna_hasta: Annotated[str | None, Form()] = None,
    permite_reintegro: Annotated[str | None, Form()] = None,
    observaciones: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
):
    nueva_regla = ReglaHora(**rule_form_data(
        convenio, tipo_dia, tipo_hora, hora_nocturna_desde,
        hora_nocturna_hasta, permite_reintegro, observaciones,
    ))
    try:
        db.add(nueva_regla)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo guardar la regla.") from error
    return RedirectResponse("/configuracion/parametros?guardado=creada", status_code=303)


@app.post("/configuracion/parametros/reglas/{regla_id}")
def actualizar_regla(
    regla_id: int,
    convenio: Annotated[str, Form()],
    tipo_dia: Annotated[str, Form()],
    tipo_hora: Annotated[str, Form()],
    hora_nocturna_desde: Annotated[str | None, Form()] = None,
    hora_nocturna_hasta: Annotated[str | None, Form()] = None,
    permite_reintegro: Annotated[str | None, Form()] = None,
    observaciones: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
):
    regla = db.get(ReglaHora, regla_id)
    if regla is None:
        raise HTTPException(status_code=404, detail="La regla no existe.")
    for field, value in rule_form_data(
        convenio, tipo_dia, tipo_hora, hora_nocturna_desde,
        hora_nocturna_hasta, permite_reintegro, observaciones,
    ).items():
        setattr(regla, field, value)
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo actualizar la regla.") from error
    return RedirectResponse("/configuracion/parametros?guardado=actualizada", status_code=303)


@app.get("/configuracion/usuarios", response_class=HTMLResponse)
def usuarios_y_roles(
    request: Request,
    editar_usuario: int | None = None,
    editar_rol: int | None = None,
    guardado: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    usuarios: list[Usuario] = []
    roles: list[UsuarioRol] = []
    tipos_contratacion: list[TipoContratacion] = []
    convenios: list[str] = []
    usuario_edicion = None
    rol_edicion = None
    try:
        roles = list(db.scalars(select(UsuarioRol).order_by(UsuarioRol.rol)))
        tipos_contratacion = list(db.scalars(
            select(TipoContratacion).order_by(TipoContratacion.id_tipo_contratacion)
        ))
        convenios = list(db.scalars(
            select(ReglaHora.convenio)
            .distinct()
            .order_by(ReglaHora.convenio)
        ))
        usuarios = list(db.scalars(
            select(Usuario)
            .options(selectinload(Usuario.rol), selectinload(Usuario.tipo_contratacion))
            .order_by(Usuario.apellido, Usuario.nombre)
        ))
        if editar_usuario is not None:
            usuario_edicion = db.get(Usuario, editar_usuario)
            if usuario_edicion is None:
                error = "El usuario seleccionado no existe."
        if editar_rol is not None:
            rol_edicion = db.get(UsuarioRol, editar_rol)
            if rol_edicion is None:
                error = "El rol seleccionado no existe."
    except SQLAlchemyError:
        error = "No se pudieron cargar usuarios y roles. Verificá la conexión con la base."

    return templates.TemplateResponse(request, "usuarios.html", {
        "active_page": "usuarios",
        "usuarios": usuarios,
        "roles": roles,
        "tipos_contratacion": tipos_contratacion,
        "convenios": convenios,
        "usuario_edicion": usuario_edicion,
        "rol_edicion": rol_edicion,
        "guardado": guardado,
        "error": error,
    })


@app.post("/configuracion/roles")
def crear_rol(
    rol: Annotated[str, Form()],
    perfil: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
):
    nombre_rol = rol.strip()
    if not nombre_rol:
        raise HTTPException(status_code=422, detail="El nombre del rol es obligatorio.")
    db.add(UsuarioRol(rol=nombre_rol, perfil=clean_optional(perfil)))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse("/configuracion/usuarios?error=Ya+existe+un+rol+con+ese+nombre", status_code=303)
    return RedirectResponse("/configuracion/usuarios?guardado=rol+creado", status_code=303)


@app.post("/configuracion/roles/{rol_id}")
def actualizar_rol(
    rol_id: int,
    rol: Annotated[str, Form()],
    perfil: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
):
    registro = db.get(UsuarioRol, rol_id)
    if registro is None:
        raise HTTPException(status_code=404, detail="El rol no existe.")
    registro.rol = rol.strip()
    registro.perfil = clean_optional(perfil)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse("/configuracion/usuarios?error=Ya+existe+un+rol+con+ese+nombre", status_code=303)
    return RedirectResponse("/configuracion/usuarios?guardado=rol+actualizado", status_code=303)


def update_user_fields(
    usuario: Usuario,
    legajo: str | None,
    nombre: str,
    apellido: str,
    correo: str | None,
    convenio: str | None,
    id_tipo_contratacion: int,
    observaciones: str | None,
    username: str,
    origen: str,
    perfil: str,
    status: str | None,
    id_rol: int,
) -> None:
    required = [nombre.strip(), apellido.strip(), username.strip(), origen.strip()]
    if not all(required):
        raise HTTPException(status_code=422, detail="Completá los campos obligatorios.")
    usuario.legajo = clean_optional(legajo)
    usuario.nombre = nombre.strip()
    usuario.apellido = apellido.strip()
    usuario.correo = clean_optional(correo)
    usuario.convenio = clean_optional(convenio)
    usuario.id_tipo_contratacion = id_tipo_contratacion
    usuario.observaciones = clean_optional(observaciones)
    usuario.username = username.strip()
    usuario.origen = origen.strip()
    perfil_normalizado = perfil.strip().upper()
    if perfil_normalizado not in {"USUARIO", "JEFE"}:
        raise HTTPException(status_code=422, detail="El perfil seleccionado no es válido.")
    usuario.perfil = perfil_normalizado
    usuario.status = status == "on"
    usuario.id_rol = id_rol


@app.post("/configuracion/usuarios")
def crear_usuario(
    nombre: Annotated[str, Form()],
    apellido: Annotated[str, Form()],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    origen: Annotated[str, Form()],
    perfil: Annotated[str, Form()],
    id_rol: Annotated[int, Form()],
    legajo: Annotated[str | None, Form()] = None,
    correo: Annotated[str | None, Form()] = None,
    convenio: Annotated[str | None, Form()] = None,
    id_tipo_contratacion: Annotated[int, Form()] = 0,
    observaciones: Annotated[str | None, Form()] = None,
    status: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
):
    if len(password) < 8:
        return RedirectResponse("/configuracion/usuarios?error=La+contraseña+debe+tener+al+menos+8+caracteres", status_code=303)
    if db.get(UsuarioRol, id_rol) is None:
        raise HTTPException(status_code=422, detail="El rol seleccionado no existe.")
    if db.get(TipoContratacion, id_tipo_contratacion) is None:
        raise HTTPException(status_code=422, detail="La contratación seleccionada no existe.")
    if convenio not in set(db.scalars(select(ReglaHora.convenio).distinct())):
        raise HTTPException(status_code=422, detail="El convenio seleccionado no existe en las reglas de horas.")
    usuario = Usuario(hashed_password=hash_password(password))
    update_user_fields(usuario, legajo, nombre, apellido, correo, convenio, id_tipo_contratacion, observaciones, username, origen, perfil, status, id_rol)
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse("/configuracion/usuarios?error=El+legajo,+correo+o+usuario+ya+está+registrado", status_code=303)
    return RedirectResponse("/configuracion/usuarios?guardado=usuario+creado", status_code=303)


@app.post("/configuracion/usuarios/{usuario_id}")
def actualizar_usuario(
    usuario_id: int,
    nombre: Annotated[str, Form()],
    apellido: Annotated[str, Form()],
    username: Annotated[str, Form()],
    origen: Annotated[str, Form()],
    perfil: Annotated[str, Form()],
    id_rol: Annotated[int, Form()],
    legajo: Annotated[str | None, Form()] = None,
    correo: Annotated[str | None, Form()] = None,
    convenio: Annotated[str | None, Form()] = None,
    id_tipo_contratacion: Annotated[int, Form()] = 0,
    observaciones: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
    status: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="El usuario no existe.")
    if db.get(UsuarioRol, id_rol) is None:
        raise HTTPException(status_code=422, detail="El rol seleccionado no existe.")
    if db.get(TipoContratacion, id_tipo_contratacion) is None:
        raise HTTPException(status_code=422, detail="La contratación seleccionada no existe.")
    if convenio not in set(db.scalars(select(ReglaHora.convenio).distinct())):
        raise HTTPException(status_code=422, detail="El convenio seleccionado no existe en las reglas de horas.")
    if password:
        if len(password) < 8:
            return RedirectResponse(f"/configuracion/usuarios?editar_usuario={usuario_id}&error=La+contraseña+debe+tener+al+menos+8+caracteres", status_code=303)
        usuario.hashed_password = hash_password(password)
    update_user_fields(usuario, legajo, nombre, apellido, correo, convenio, id_tipo_contratacion, observaciones, username, origen, perfil, status, id_rol)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(f"/configuracion/usuarios?editar_usuario={usuario_id}&error=El+legajo,+correo+o+usuario+ya+está+registrado", status_code=303)
    return RedirectResponse("/configuracion/usuarios?guardado=usuario+actualizado", status_code=303)


@app.get("/configuracion/feriados", response_class=HTMLResponse)
def administrar_feriados(
    request: Request,
    editar: int | None = None,
    guardado: str | None = None,
    error: str | None = None,
    anio_actualizado: int | None = None,
    cantidad: int | None = None,
    duplicados: int | None = None,
    db: Session = Depends(get_db),
):
    feriados: list[Feriado] = []
    feriado_edicion = None
    try:
        feriados = list(db.scalars(select(Feriado).order_by(Feriado.fecha)))
        if editar is not None:
            feriado_edicion = db.get(Feriado, editar)
            if feriado_edicion is None:
                error = "El feriado seleccionado no existe"
    except SQLAlchemyError:
        error = "No se pudieron cargar los feriados. Verificá la conexión con la base"
    return templates.TemplateResponse(request, "feriados.html", {
        "active_page": "feriados",
        "feriados": feriados,
        "feriado_edicion": feriado_edicion,
        "guardado": guardado,
        "error": error,
        "anio_actualizado": anio_actualizado,
        "cantidad": cantidad or 0,
        "duplicados": duplicados or 0,
        "anio_actualizacion": min(
            (feriado.fecha.year for feriado in feriados),
            default=None,
        ),
    })


@app.post("/configuracion/feriados")
def crear_feriado(
    fecha: Annotated[date, Form()],
    observacion: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    observacion = observacion.strip()
    if not observacion:
        raise HTTPException(status_code=422, detail="La observación es obligatoria.")
    db.add(Feriado(fecha=fecha, observacion=observacion))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse("/configuracion/feriados?error=Ya+existe+un+feriado+en+esa+fecha", status_code=303)
    return RedirectResponse("/configuracion/feriados?guardado=creado", status_code=303)


@app.post("/configuracion/feriados/actualizar-anio")
def actualizar_anio_feriados(
    anio_origen: Annotated[int, Form()],
    db: Session = Depends(get_db),
):
    if anio_origen < 1900 or anio_origen > 9998:
        raise HTTPException(status_code=422, detail="El año indicado no es válido.")
    feriados_origen = list(db.scalars(
        select(Feriado)
        .where(
            Feriado.fecha >= date(anio_origen, 1, 1),
            Feriado.fecha <= date(anio_origen, 12, 31),
        )
        .order_by(Feriado.fecha)
    ))
    if not feriados_origen:
        return RedirectResponse(
            "/configuracion/feriados?error=No+hay+feriados+para+el+año+seleccionado",
            status_code=303,
        )

    anio_destino = anio_origen + 1
    fechas_destino = {
        feriado.fecha: feriado
        for feriado in db.scalars(
            select(Feriado).where(
                Feriado.fecha >= date(anio_destino, 1, 1),
                Feriado.fecha <= date(anio_destino, 12, 31),
            )
        )
    }
    actualizados = 0
    duplicados = 0
    try:
        for feriado in feriados_origen:
            try:
                nueva_fecha = feriado.fecha.replace(year=anio_destino)
            except ValueError as error:
                raise HTTPException(
                    status_code=422,
                    detail=f"La fecha {feriado.fecha.strftime('%d/%m/%Y')} no existe en {anio_destino}.",
                ) from error
            if nueva_fecha in fechas_destino:
                db.delete(feriado)
                duplicados += 1
            else:
                feriado.fecha = nueva_fecha
                fechas_destino[nueva_fecha] = feriado
                actualizados += 1
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo actualizar el año de los feriados.") from error
    return RedirectResponse(
        f"/configuracion/feriados?anio_actualizado={anio_destino}&cantidad={actualizados}&duplicados={duplicados}",
        status_code=303,
    )


@app.post("/configuracion/feriados/{feriado_id}")
def actualizar_feriado(
    feriado_id: int,
    fecha: Annotated[date, Form()],
    observacion: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    feriado = db.get(Feriado, feriado_id)
    if feriado is None:
        raise HTTPException(status_code=404, detail="El feriado no existe.")
    feriado.fecha = fecha
    feriado.observacion = observacion.strip()
    if not feriado.observacion:
        raise HTTPException(status_code=422, detail="La observación es obligatoria.")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(
            f"/configuracion/feriados?editar={feriado_id}&error=Ya+existe+un+feriado+en+esa+fecha",
            status_code=303,
        )
    return RedirectResponse("/configuracion/feriados?guardado=actualizado", status_code=303)


@app.get("/autorizaciones", response_class=HTMLResponse)
def autorizaciones(
    request: Request,
    jefe_id: int | None = None,
    editar: int | None = None,
    guardado: int | None = None,
    rechazado: int | None = None,
    db: Session = Depends(get_db),
):
    jefes = list(db.scalars(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(Usuario.status.is_(True), Usuario.perfil == "JEFE")
        .order_by(Usuario.apellido, Usuario.nombre)
    ))
    jefe = None
    grupos = []
    hora_edicion = None
    if jefe_id is not None:
        jefe = obtener_jefe(jefe_id, db)
        pendientes = list(db.scalars(
            select(HoraExtra)
            .join(HoraExtra.usuario)
            .options(selectinload(HoraExtra.usuario))
            .where(
                HoraExtra.estado == "PENDIENTE",
                Usuario.id_rol == jefe.id_rol,
                Usuario.id != jefe.id,
            )
            .order_by(Usuario.apellido, Usuario.nombre, HoraExtra.fecha, HoraExtra.hora_inicio)
        ))
        agrupados: dict[int, dict] = {}
        for hora in pendientes:
            grupo = agrupados.setdefault(hora.usuario_id, {
                "usuario": hora.usuario,
                "horas": [],
                "total": Decimal("0.00"),
            })
            grupo["horas"].append(hora)
            grupo["total"] += hora.horas_totales
        grupos = list(agrupados.values())

        if editar is not None:
            hora_edicion = db.scalar(
                select(HoraExtra)
                .options(selectinload(HoraExtra.usuario))
                .where(HoraExtra.id == editar)
            )
            validar_hora_para_jefe(hora_edicion, jefe)

    return templates.TemplateResponse(request, "autorizaciones.html", {
        "active_page": "autorizaciones",
        "jefes": jefes,
        "jefe": jefe,
        "grupos": grupos,
        "hora_edicion": hora_edicion,
        "guardado": guardado,
        "rechazado": rechazado,
        "cantidad_pendientes": sum(len(grupo["horas"]) for grupo in grupos),
        "total_pendiente": sum(
            (grupo["total"] for grupo in grupos),
            start=Decimal("0.00"),
        ),
    })


@app.post("/autorizaciones/aprobar")
def aprobar_horas(
    jefe_id: Annotated[int, Form()],
    hora_ids: Annotated[list[int] | None, Form()] = None,
    db: Session = Depends(get_db),
):
    ids = list(dict.fromkeys(hora_ids or []))
    if not ids:
        raise HTTPException(status_code=422, detail="Seleccioná al menos una carga para autorizar.")
    jefe = obtener_jefe(jefe_id, db)
    try:
        horas = list(db.scalars(
            select(HoraExtra)
            .options(selectinload(HoraExtra.usuario))
            .where(HoraExtra.id.in_(ids))
            .with_for_update()
        ))
        if len(horas) != len(ids):
            raise HTTPException(status_code=404, detail="Una de las cargas seleccionadas no existe.")
        for hora in horas:
            validar_hora_para_jefe(hora, jefe)
            hora.estado = "APROBADA"
            hora.aprobado_por = jefe.id
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudieron autorizar las horas seleccionadas.") from error
    return RedirectResponse(
        f"/autorizaciones?jefe_id={jefe.id}&guardado={len(horas)}",
        status_code=303,
    )


@app.post("/autorizaciones/rechazar")
def rechazar_horas(
    jefe_id: Annotated[int, Form()],
    hora_ids: Annotated[list[int] | None, Form()] = None,
    db: Session = Depends(get_db),
):
    ids = list(dict.fromkeys(hora_ids or []))
    if not ids:
        raise HTTPException(status_code=422, detail="Seleccioná al menos una carga para rechazar.")
    jefe = obtener_jefe(jefe_id, db)
    try:
        horas = list(db.scalars(
            select(HoraExtra)
            .options(selectinload(HoraExtra.usuario))
            .where(HoraExtra.id.in_(ids))
            .with_for_update()
        ))
        if len(horas) != len(ids):
            raise HTTPException(status_code=404, detail="Una de las cargas seleccionadas no existe.")
        for hora in horas:
            validar_hora_para_jefe(hora, jefe)
            hora.estado = "RECHAZADA"
            hora.aprobado_por = jefe.id
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail="No se pudieron rechazar las horas seleccionadas.") from error
    return RedirectResponse(
        f"/autorizaciones?jefe_id={jefe.id}&rechazado={len(horas)}",
        status_code=303,
    )


@app.post("/autorizaciones/{hora_id}/editar")
def editar_hora_pendiente(
    hora_id: int,
    jefe_id: Annotated[int, Form()],
    fecha: Annotated[date, Form()],
    hora_inicio: Annotated[time, Form()],
    hora_fin: Annotated[time, Form()],
    observaciones: Annotated[str | None, Form()] = None,
    solicita_reintegro: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
):
    jefe = obtener_jefe(jefe_id, db)
    hora = db.scalar(
        select(HoraExtra)
        .options(selectinload(HoraExtra.usuario))
        .where(HoraExtra.id == hora_id)
    )
    validar_hora_para_jefe(hora, jefe)
    try:
        resultado = calcular_resultado_horas_extra(
            hora.usuario_id, fecha, hora_inicio, hora_fin, db,
        )
        hora.fecha = resultado.fecha
        hora.hora_inicio = resultado.hora_inicio
        hora.hora_fin = resultado.hora_fin
        hora.horas_totales = resultado.horas_totales
        hora.tipo_dia = resultado.tipo_dia
        hora.tipo_hora = resultado.tipo_hora
        hora.horas_nocturnas = resultado.horas_nocturnas
        hora.solicita_reintegro = (
            resultado.permite_reintegro and solicita_reintegro == "on"
        )
        hora.observaciones = clean_optional(observaciones)
        db.commit()
    except (CalculoHorasError, SQLAlchemyError) as error:
        db.rollback()
        mensaje = str(error) if isinstance(error, CalculoHorasError) else "No se pudo actualizar la carga."
        raise HTTPException(status_code=422, detail=mensaje) from error
    return RedirectResponse(f"/autorizaciones?jefe_id={jefe.id}", status_code=303)


@app.get("/health")
def health_check():
    return {"estado": "ok", "aplicacion": "activa"}


@app.get("/health/db")
@app.get("/health/database")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"estado": "ok", "base_de_datos": "conectada"}
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail={"estado": "error", "base_de_datos": "desconectada"},
        ) from error
