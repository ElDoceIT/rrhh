import os
import unittest
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app.database.connection import Base
from app.database.models import (
    ConceptoExcepcional,
    Feriado,
    HoraExtra,
    ReglaHora,
    TipoContratacion,
    Usuario,
    UsuarioConceptoExcepcional,
    UsuarioRol,
)
from app.services.local_auth import (
    authenticate_local_user,
    is_local_username,
    seed_local_admin,
    session_user,
)
from app.services.calculo_horas import (
    CalculoHorasError,
    calcular_horas_totales,
    calcular_resultado_concepto_excepcional,
    calcular_resultado_dia_trabajado,
    calcular_resultado_domingo,
    calcular_resultado_horas_extra,
    calcular_resultado_otra_carga,
    calcular_resultado_reintegro,
    clasificar_tipo_dia,
    dividir_carga_en_fechas,
)
from app.services.access_catalog import CONVENIOS_DISPONIBLES, PERFILES_DISPONIBLES, ROLES_DISPONIBLES
from app.main import (
    app,
    confirmar_solicitud,
    detalle_exportacion_rrhh,
    encode_carga,
    expandir_ids_con_jornadas_pendientes,
    filas_exportacion_rrhh,
    ids_habilitados_para_confirmar,
    limites_fecha_carga_usuario,
    obtener_autorizador,
    procesar_solicitud,
    recalcular_conceptos_jornada_pendiente,
    rechazar_horas,
    usuarios_habilitados_para_carga,
)
from fastapi import HTTPException


class LocalAuthTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(engine)

    @patch.dict(os.environ, {
        "AUTH_LOCAL_USERS": " admin, ROOT ",
        "SEED_ADMIN_USERNAME": "Admin",
        "SEED_ADMIN_PASSWORD": "una-clave-segura",
    }, clear=False)
    def test_seed_is_idempotent_and_authentication_is_case_insensitive(self):
        with self.Session() as db:
            self.assertTrue(seed_local_admin(db))
            original = db.query(Usuario).one()
            original_hash = original.hashed_password
            original_roles = [(item.rol, item.perfil) for item in original.roles]

            self.assertFalse(seed_local_admin(db))
            self.assertEqual(db.query(Usuario).count(), 1)
            stored = db.query(Usuario).one()
            self.assertEqual(stored.hashed_password, original_hash)
            self.assertEqual(
                [(item.rol, item.perfil) for item in stored.roles],
                original_roles,
            )
            self.assertEqual(original_roles, [("ADMIN", "JEFE")])
            self.assertIsNotNone(authenticate_local_user(db, "ADMIN", "una-clave-segura"))
            self.assertIsNone(authenticate_local_user(db, "admin", "incorrecta"))
            self.assertTrue(is_local_username(" Root "))

    @patch.dict(os.environ, {"AUTH_LOCAL_USERS": "admin"}, clear=False)
    def test_seed_without_password_does_nothing(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SEED_ADMIN_PASSWORD", None)
            with self.Session() as db:
                self.assertFalse(seed_local_admin(db))
                self.assertEqual(db.query(Usuario).count(), 0)
                self.assertEqual(db.query(UsuarioRol).count(), 0)

    def test_access_catalog_is_fixed(self):
        self.assertEqual(ROLES_DISPONIBLES, (
            "COMERCIAL", "DIGITAL", "REALIZACIONES", "ADMIN",
            "NOTICIERO", "RRHH", "TECNICA", "IT",
        ))
        self.assertEqual(PERFILES_DISPONIBLES, ("USUARIO", "JEFE"))
        self.assertEqual(CONVENIOS_DISPONIBLES, ("CISPREN", "SAL", "SAT", "FC"))

    def test_load_date_limits_follow_contract_type(self):
        nomina = Usuario(
            nombre="N", apellido="N", username="nomina-periodo",
            hashed_password="x", origen="AD", status=True,
            tipo_contratacion=TipoContratacion(contratacion="Nómina"),
        )
        monotributo = Usuario(
            nombre="M", apellido="M", username="mono-periodo",
            hashed_password="x", origen="AD", status=True,
            tipo_contratacion=TipoContratacion(contratacion="Monotributo"),
        )
        self.assertEqual(
            limites_fecha_carga_usuario(nomina, date(2026, 8, 10))[:2],
            (date(2026, 7, 16), date(2026, 8, 15)),
        )
        self.assertEqual(
            limites_fecha_carga_usuario(nomina, date(2026, 8, 21))[:2],
            (date(2026, 8, 16), date(2026, 9, 15)),
        )
        self.assertEqual(
            limites_fecha_carga_usuario(monotributo, date(2026, 8, 21))[:2],
            (date(2026, 8, 1), date(2026, 8, 31)),
        )

    def test_exceptional_concept_requires_valid_assignment_and_half_units(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="ana-excepcion",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            concept = ConceptoExcepcional(
                nombre="Plus operativo", descripcion="Tarea especial", activo=True,
            )
            db.add_all([user, concept])
            db.flush()

            with self.assertRaisesRegex(CalculoHorasError, "No tenés habilitado"):
                calcular_resultado_concepto_excepcional(
                    user.id, date(2026, 8, 20), concept.id_concepto_excepcional,
                    Decimal("1.00"), db,
                )

            db.add(UsuarioConceptoExcepcional(
                usuario_id=user.id,
                concepto_excepcional_id=concept.id_concepto_excepcional,
                fecha_desde=date(2026, 8, 16),
                fecha_hasta=date(2026, 9, 15),
                activo=True,
                observacion="Autorizado por RRHH",
            ))
            db.flush()

            with self.assertRaisesRegex(CalculoHorasError, "de a 0,5"):
                calcular_resultado_concepto_excepcional(
                    user.id, date(2026, 8, 20), concept.id_concepto_excepcional,
                    Decimal("1.20"), db,
                )

            result = calcular_resultado_concepto_excepcional(
                user.id, date(2026, 8, 20), concept.id_concepto_excepcional,
                Decimal("1.50"), db,
            )
            self.assertEqual(result.tipo_registro, "EXCEPCIONAL")
            self.assertEqual(result.cantidad, Decimal("1.50"))
            self.assertEqual(result.concepto_excepcional_nombre, "Plus operativo")

    def test_session_contains_all_assignments_and_selects_one(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Juan",
                apellido="Pérez",
                username="jperez",
                hashed_password="sin-uso",
                origen="AD",
                status=True,
            )
            user.roles.extend([
                UsuarioRol(rol="RRHH", perfil="USUARIO"),
                UsuarioRol(rol="OPERACIONES", perfil="JEFE"),
            ])
            db.add(user)
            db.commit()

            data = session_user(user, "AD")
            self.assertEqual(len(data["assignments"]), 2)
            self.assertEqual(data["role"], "OPERACIONES")
            self.assertEqual(data["profile"], "JEFE")
            self.assertEqual(data["active_assignment_id"], data["assignments"][0]["id"])

    def test_only_regular_users_can_load_their_own_hours(self):
        with self.Session() as db:
            jefe = Usuario(nombre="Jefa", apellido="Comercial", username="jefa", hashed_password="x", origen="AD", status=True)
            empleado = Usuario(nombre="Empleado", apellido="Comercial", username="empleado", hashed_password="x", origen="AD", status=True)
            externo = Usuario(nombre="Empleado", apellido="RRHH", username="externo", hashed_password="x", origen="AD", status=True)
            jefe.roles.append(UsuarioRol(rol="COMERCIAL", perfil="JEFE"))
            empleado.roles.append(UsuarioRol(rol="COMERCIAL", perfil="USUARIO"))
            externo.roles.append(UsuarioRol(rol="RRHH", perfil="USUARIO"))
            db.add_all([jefe, empleado, externo])
            db.commit()

            request = Request({
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": [],
                "session": {
                    "user": {
                        "id": jefe.id,
                        "active_assignment_id": jefe.roles[0].id_rol,
                    }
                },
            })
            with self.assertRaisesRegex(HTTPException, "Sólo los usuarios"):
                usuarios_habilitados_para_carga(request, db, "otro")
            with self.assertRaisesRegex(HTTPException, "Sólo los usuarios"):
                ids_habilitados_para_confirmar(request, db)
            actor, assignment, is_admin = obtener_autorizador(request, db)
            self.assertEqual(actor.id, jefe.id)
            self.assertEqual(assignment.rol, "COMERCIAL")
            self.assertFalse(is_admin)

            employee_request = Request({
                "type": "http", "method": "GET", "path": "/solicitudes/nueva",
                "headers": [],
                "session": {"user": {
                    "id": empleado.id,
                    "active_assignment_id": empleado.roles[0].id_rol,
                }},
            })
            _, allowed = usuarios_habilitados_para_carga(employee_request, db, "otro")
            self.assertEqual([item.id for item in allowed], [empleado.id])
            self.assertEqual(ids_habilitados_para_confirmar(employee_request, db), {empleado.id})

    def test_regular_user_cannot_access_authorizations_and_admin_can(self):
        with self.Session() as db:
            regular = Usuario(nombre="Usuario", apellido="Común", username="comun", hashed_password="x", origen="AD", status=True)
            admin = Usuario(nombre="Admin", apellido="Local", username="admin2", hashed_password="x", origen="LOCAL", status=True)
            regular.roles.append(UsuarioRol(rol="RRHH", perfil="USUARIO"))
            admin.roles.append(UsuarioRol(rol="ADMIN", perfil="USUARIO"))
            db.add_all([regular, admin])
            db.commit()

            def request_for(user):
                return Request({
                    "type": "http", "method": "GET", "path": "/autorizaciones", "headers": [],
                    "session": {"user": {"id": user.id, "active_assignment_id": user.roles[0].id_rol}},
                })

            with self.assertRaises(HTTPException):
                obtener_autorizador(request_for(regular), db)
            _, assignment, is_admin = obtener_autorizador(request_for(admin), db)
            self.assertEqual(assignment.rol, "ADMIN")
            self.assertTrue(is_admin)

    def test_rejection_saves_its_own_observation_and_resolution_date(self):
        with self.Session() as db:
            jefe = Usuario(nombre="Jefa", apellido="Comercial", username="jefa-rechazo", hashed_password="x", origen="AD", status=True)
            empleado = Usuario(nombre="Empleado", apellido="Comercial", username="empleado-rechazo", hashed_password="x", origen="AD", status=True)
            jefe.roles.append(UsuarioRol(rol="COMERCIAL", perfil="JEFE"))
            empleado.roles.append(UsuarioRol(rol="COMERCIAL", perfil="USUARIO"))
            db.add_all([jefe, empleado])
            db.flush()
            hora = HoraExtra(
                usuario_id=empleado.id, fecha=date(2026, 8, 21),
                hora_inicio=time(18, 0), hora_fin=time(20, 0),
                horas_totales=Decimal("2.00"), tipo_dia="HABIL",
                tipo_hora="50", estado="PENDIENTE",
            )
            db.add(hora)
            db.commit()
            request = Request({
                "type": "http", "method": "POST", "path": "/autorizaciones/rechazar",
                "headers": [],
                "session": {"user": {
                    "id": jefe.id,
                    "active_assignment_id": jefe.roles[0].id_rol,
                }},
            })

            response = rechazar_horas(
                request=request,
                hora_ids=[hora.id],
                fila_ids=[hora.id],
                observaciones_rechazo=["  Horario sin justificar  "],
                db=db,
            )

            db.refresh(hora)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(hora.estado, "RECHAZADA")
            self.assertEqual(hora.aprobado_por, jefe.id)
            self.assertEqual(hora.observacion_rechazo, "Horario sin justificar")
            self.assertIsNotNone(hora.fecha_resolucion)

    def test_confirmation_rejects_a_load_without_observation(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="sin-observacion",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            user.roles.append(UsuarioRol(rol="COMERCIAL", perfil="USUARIO"))
            db.add_all([
                user,
                ReglaHora(convenio="SAT", tipo_dia="HABIL", tipo_hora="50"),
            ])
            db.commit()
            request = Request({
                "type": "http", "method": "POST", "path": "/solicitudes/confirmar",
                "headers": [],
                "session": {"user": {
                    "id": user.id,
                    "active_assignment_id": user.roles[0].id_rol,
                }},
            })
            carga = encode_carga(
                user.id, date(2026, 8, 21), time(18, 0), time(20, 0), None,
            )
            with self.assertRaisesRegex(HTTPException, "observación"):
                confirmar_solicitud(
                    request=request, cargas=[carga], reintegros=["NO"], db=db,
                )


class MidnightSplitTests(unittest.TestCase):
    def test_times_must_use_half_hour_intervals(self):
        with self.assertRaisesRegex(CalculoHorasError, "30 minutos"):
            calcular_resultado_horas_extra(
                1, date(2026, 8, 6), time(22, 15), time(23, 0), None
            )


class ExportacionTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(engine)

    def test_export_includes_hours_days_reimbursements_concepts_and_night_hours(self):
        with self.Session() as db:
            usuario = Usuario(
                nombre="Ana", apellido="Exportación", username="exportacion-total",
                hashed_password="x", origen="AD", status=True, convenio="SAT",
            )
            db.add(usuario)
            db.flush()
            db.add_all([
                HoraExtra(
                    usuario_id=usuario.id, fecha=date(2026, 8, 20),
                    hora_inicio=time(18), hora_fin=time(23),
                    horas_totales=Decimal("5"), horas_nocturnas=Decimal("1"),
                    tipo_dia="HABIL", tipo_hora="50", tipo_registro="HORAS",
                    estado="APROBADA",
                ),
                HoraExtra(
                    usuario_id=usuario.id, fecha=date(2026, 8, 20),
                    cantidad=Decimal("1"), tipo_dia="HABIL", tipo_hora="COMIDA",
                    tipo_registro="OTRAS", estado="APROBADA",
                ),
                HoraExtra(
                    usuario_id=usuario.id, fecha=date(2026, 8, 21),
                    tipo_dia="FRANCO", tipo_registro="DIA_TRABAJADO",
                    estado="APROBADA",
                ),
                HoraExtra(
                    usuario_id=usuario.id, fecha=date(2026, 8, 22),
                    tipo_dia="FERIADO", tipo_registro="REINTEGRO",
                    estado="APROBADA",
                ),
            ])
            db.commit()

            filas = filas_exportacion_rrhh(
                db, date(2026, 8, 16), date(2026, 9, 15), [], [],
            )
            conceptos = {fila.tipo_hora: fila.cantidad for fila in filas}

            self.assertEqual(conceptos, {
                "50": Decimal("5"),
                "COMIDA": Decimal("1"),
                "FRANCO TRABAJADO": Decimal("1"),
                "HORAS NOCTURNAS": Decimal("1"),
                "REINTEGRO FERIADO": Decimal("1"),
            })
            detalle = detalle_exportacion_rrhh(
                db, date(2026, 8, 16), date(2026, 9, 15), [], [],
            )
            self.assertEqual(len(detalle), 5)
            self.assertTrue(all(fila.fecha is not None for fila in detalle))


class ReintegroTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(engine)

    def test_reintegro_has_no_hours_and_requires_allowed_rule(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez",
                hashed_password="x", origen="AD", convenio="SATSAID", status=True,
            )
            db.add_all([
                user,
                ReglaHora(
                    convenio="SATSAID", tipo_dia="FRANCO", tipo_hora="100",
                    permite_reintegro=True,
                ),
            ])
            db.commit()
            result = calcular_resultado_reintegro(user.id, date(2026, 8, 9), db)
            self.assertEqual(result.tipo_registro, "REINTEGRO")
            self.assertIsNone(result.hora_inicio)
            self.assertIsNone(result.horas_totales)
            self.assertTrue(result.permite_reintegro)

    def test_weekend_is_not_automatically_franco(self):
        with self.Session() as db:
            self.assertEqual(clasificar_tipo_dia(date(2026, 8, 8), db), "HABIL")
            self.assertEqual(clasificar_tipo_dia(date(2026, 8, 9), db), "HABIL")

    def test_worked_day_requires_holiday_or_explicit_franco(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez-dia-trabajado",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            db.add(user)
            db.commit()
            with self.assertRaisesRegex(CalculoHorasError, "Indicá que corresponde a un franco"):
                calcular_resultado_dia_trabajado(
                    user.id, date(2026, 8, 21), db,
                )
            result = calcular_resultado_dia_trabajado(
                user.id, date(2026, 8, 21), db, marcar_como_franco=True,
            )
            self.assertEqual(result.tipo_registro, "DIA_TRABAJADO")
            self.assertEqual(result.tipo_dia, "FRANCO")
            self.assertIsNone(result.horas_totales)

    def test_worked_day_schedule_calculates_total_and_cross_midnight_night_hours(self):
        with self.Session() as db:
            usuario = Usuario(
                nombre="Ana", apellido="SAT", username="sat-jornada",
                hashed_password="x", origen="AD", status=True, convenio="SAT",
            )
            db.add_all([
                usuario,
                ReglaHora(
                    convenio="SAT", tipo_dia="FRANCO", tipo_hora="100",
                    hora_nocturna_desde=time(22, 0), hora_nocturna_hasta=time(6, 0),
                ),
                ReglaHora(
                    convenio="SAT", tipo_dia="HABIL", tipo_hora="50",
                    hora_nocturna_desde=time(22, 0), hora_nocturna_hasta=time(6, 0),
                ),
            ])
            db.flush()

            result = calcular_resultado_dia_trabajado(
                usuario.id, date(2026, 8, 29), db,
                marcar_como_franco=True,
                hora_inicio=time(23, 30), hora_fin=time(7, 0),
            )

            self.assertEqual(result.horas_totales, Decimal("7.50"))
            self.assertEqual(result.horas_nocturnas, Decimal("6.50"))
            self.assertEqual(result.hora_inicio, time(23, 30))
            self.assertEqual(result.hora_fin, time(7, 0))

    def test_short_franco_becomes_actual_hours_at_100_and_four_hours_becomes_day(self):
        with self.Session() as db:
            usuario = Usuario(
                nombre="Ana", apellido="Franco", username="umbral-franco",
                hashed_password="x", origen="AD", status=True, convenio="SAT",
            )
            usuario.roles.append(UsuarioRol(rol="COMERCIAL", perfil="USUARIO"))
            db.add_all([
                usuario,
                ReglaHora(convenio="SAT", tipo_dia="FRANCO", tipo_hora="100"),
                ReglaHora(convenio="SAT", tipo_dia="TODOS", tipo_hora="MERIENDA"),
                ReglaHora(convenio="SAT", tipo_dia="TODOS", tipo_hora="COMIDA"),
            ])
            db.commit()
            request = Request({
                "type": "http", "method": "POST", "path": "/solicitudes/procesar",
                "headers": [], "app": app,
                "session": {"user": {
                    "id": usuario.id,
                    "active_assignment_id": usuario.roles[0].id_rol,
                }},
            })

            corto = procesar_solicitud(
                request=request,
                usuario_id=usuario.id,
                fecha=[date(2026, 8, 29)],
                tipo_registro="DIA_TRABAJADO",
                jornada_hora_inicio=time(8, 0),
                jornada_hora_fin=time(11, 30),
                observaciones="Franco corto",
                db=db,
            )
            self.assertEqual(len(corto.context["resultados"]), 1)
            self.assertEqual(corto.context["resultados"][0].tipo_registro, "HORAS")
            self.assertEqual(corto.context["resultados"][0].tipo_hora, "100")
            self.assertEqual(corto.context["resultados"][0].horas_totales, Decimal("3.50"))

            completo = procesar_solicitud(
                request=request,
                usuario_id=usuario.id,
                fecha=[date(2026, 8, 29)],
                tipo_registro="DIA_TRABAJADO",
                jornada_hora_inicio=time(8, 0),
                jornada_hora_fin=time(12, 0),
                observaciones="Franco trabajado",
                db=db,
            )
            self.assertEqual(len(completo.context["resultados"]), 1)
            self.assertEqual(completo.context["resultados"][0].tipo_registro, "DIA_TRABAJADO")
            self.assertEqual(completo.context["resultados"][0].horas_totales, Decimal("4.00"))

            confirmar_solicitud(
                request=request,
                cargas=corto.context["cargas"],
                reintegros=corto.context["reintegros"],
                db=db,
            )
            conceptos = {
                hora.tipo_hora: hora.cantidad
                for hora in db.scalars(select(HoraExtra).where(
                    HoraExtra.usuario_id == usuario.id,
                    HoraExtra.tipo_registro == "OTRAS",
                ))
            }
            self.assertEqual(conceptos, {
                "MERIENDA": Decimal("1.00"),
                "COMIDA": Decimal("1.00"),
            })

    def test_holiday_takes_precedence_over_franco_checkbox(self):
        with self.Session() as db:
            holiday = date(2026, 8, 17)
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez-feriado",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            db.add_all([
                user,
                Feriado(fecha=holiday, observacion="Feriado de prueba"),
                ReglaHora(convenio="SAT", tipo_dia="FERIADO", tipo_hora="100"),
            ])
            db.commit()
            worked_day = calcular_resultado_dia_trabajado(
                user.id, holiday, db, marcar_como_franco=True,
            )
            extra_hours = calcular_resultado_horas_extra(
                user.id, holiday, time(18, 0), time(20, 0), db,
                marcar_como_franco=True,
            )
            self.assertEqual(worked_day.tipo_dia, "FERIADO")
            self.assertEqual(extra_hours.tipo_dia, "FERIADO")

    def test_otra_carga_uses_manual_quantity_without_hour_calculation(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez-otra",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            db.add_all([
                user,
                ReglaHora(convenio="SAT", tipo_dia="TODOS", tipo_hora="HS ARTICULO"),
            ])
            db.commit()
            result = calcular_resultado_otra_carga(
                user.id, date(2026, 8, 10), "HS ARTICULO", Decimal("8"), db,
            )
            self.assertEqual(result.tipo_registro, "OTRAS")
            self.assertEqual(result.tipo_dia, "HABIL")
            self.assertEqual(result.cantidad, Decimal("8.00"))
            self.assertIsNone(result.hora_inicio)
            self.assertIsNone(result.horas_totales)

    def test_exterior_prensa_only_accepts_three_or_six(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez-exterior",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            db.add_all([
                user,
                ReglaHora(
                    convenio="SAT", tipo_dia="TODOS", tipo_hora="EXTERIOR PRENSA",
                ),
                ReglaHora(
                    convenio="SAT", tipo_dia="TODOS", tipo_hora="EXTERIOR COMUN",
                ),
            ])
            db.commit()
            for cantidad in (Decimal("3"), Decimal("6")):
                result = calcular_resultado_otra_carga(
                    user.id, date(2026, 8, 10), "EXTERIOR PRENSA", cantidad, db,
                )
                self.assertEqual(result.cantidad, cantidad.quantize(Decimal("0.01")))
            with self.assertRaisesRegex(CalculoHorasError, "sólo admite"):
                calcular_resultado_otra_carga(
                    user.id, date(2026, 8, 10), "EXTERIOR PRENSA", Decimal("4"), db,
                )
            comun = calcular_resultado_otra_carga(
                user.id, date(2026, 8, 10), "EXTERIOR COMUN", Decimal("4"), db,
            )
            self.assertEqual(comun.cantidad, Decimal("4.00"))

    def test_sunday_concept_is_automatic_for_sat_and_has_no_reimbursement(self):
        with self.Session() as db:
            sunday = date(2026, 8, 23)
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez-domingo",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            db.add_all([
                user,
                ReglaHora(convenio="SAT", tipo_dia="TODOS", tipo_hora="DOMINGO"),
            ])
            db.commit()
            result = calcular_resultado_domingo(user.id, sunday, db)
            self.assertEqual(result.tipo_hora, "DOMINGO")
            self.assertEqual(result.cantidad, Decimal("1.00"))
            self.assertFalse(result.permite_reintegro)
            with self.assertRaisesRegex(CalculoHorasError, "no está permitido"):
                calcular_resultado_otra_carga(
                    user.id, sunday, "DOMINGO", Decimal("1"), db,
                )

    def test_hours_can_be_marked_as_franco_explicitly(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez-franco",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            db.add_all([
                user,
                ReglaHora(convenio="SAT", tipo_dia="FRANCO", tipo_hora="100"),
            ])
            db.commit()
            result = calcular_resultado_horas_extra(
                user.id, date(2026, 8, 10), time(9, 0), time(10, 0), db,
                marcar_como_franco=True,
            )
            self.assertEqual(result.tipo_dia, "FRANCO")

    def test_reintegro_on_non_holiday_is_treated_as_franco(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez-reintegro",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            db.add_all([
                user,
                ReglaHora(
                    convenio="SAT", tipo_dia="FRANCO", tipo_hora="100",
                    permite_reintegro=True,
                ),
            ])
            db.commit()
            result = calcular_resultado_reintegro(user.id, date(2026, 8, 10), db)
            self.assertEqual(result.tipo_dia, "FRANCO")

    def test_holiday_without_return_rejects_reimbursement(self):
        with self.Session() as db:
            holiday = date(2026, 8, 17)
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez-sin-devolucion",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            db.add_all([
                user,
                Feriado(
                    fecha=holiday,
                    observacion="Feriado sin devolución",
                    devuelve=False,
                ),
                ReglaHora(
                    convenio="SAT", tipo_dia="FERIADO", tipo_hora="100",
                    permite_reintegro=True,
                ),
            ])
            db.commit()
            with self.assertRaisesRegex(CalculoHorasError, "no permite solicitar reintegro"):
                calcular_resultado_reintegro(user.id, holiday, db)

    def test_crossing_midnight_creates_two_real_date_segments(self):
        segments = dividir_carga_en_fechas(
            date(2026, 8, 6), time(22, 0), time(3, 0)
        )
        self.assertEqual(segments, [
            (date(2026, 8, 6), time(22, 0), time(0, 0)),
            (date(2026, 8, 7), time(0, 0), time(3, 0)),
        ])
        self.assertEqual(calcular_horas_totales(*segments[0][1:]), Decimal("2.00"))
        self.assertEqual(calcular_horas_totales(*segments[1][1:]), Decimal("3.00"))

    def test_meals_are_recalculated_per_pending_journey(self):
        with self.Session() as db:
            user = Usuario(
                nombre="Ana", apellido="Pérez", username="aperez-comidas",
                hashed_password="x", origen="AD", convenio="SAT", status=True,
            )
            db.add_all([
                user,
                ReglaHora(convenio="SAT", tipo_dia="TODOS", tipo_hora="MERIENDA"),
                ReglaHora(convenio="SAT", tipo_dia="TODOS", tipo_hora="COMIDA"),
            ])
            db.flush()
            db.add_all([
                HoraExtra(
                    usuario_id=user.id, fecha=date(2026, 8, 20),
                    hora_inicio=time(22), hora_fin=time(0),
                    horas_totales=Decimal("2"), tipo_dia="HABIL",
                    tipo_hora="50", tipo_registro="HORAS", estado="PENDIENTE",
                ),
                HoraExtra(
                    usuario_id=user.id, fecha=date(2026, 8, 21),
                    hora_inicio=time(0), hora_fin=time(3),
                    horas_totales=Decimal("3"), tipo_dia="HABIL",
                    tipo_hora="50", tipo_registro="HORAS", estado="PENDIENTE",
                ),
                HoraExtra(
                    usuario_id=user.id, fecha=date(2026, 8, 21),
                    hora_inicio=time(18), hora_fin=time(20),
                    horas_totales=Decimal("2"), tipo_dia="HABIL",
                    tipo_hora="50", tipo_registro="HORAS", estado="PENDIENTE",
                ),
            ])
            db.flush()
            recalcular_conceptos_jornada_pendiente(user.id, date(2026, 8, 20), db)
            recalcular_conceptos_jornada_pendiente(user.id, date(2026, 8, 21), db)
            db.flush()
            concepts = list(db.query(HoraExtra).filter(
                HoraExtra.tipo_registro == "OTRAS",
            ).order_by(HoraExtra.fecha, HoraExtra.tipo_hora))
            self.assertEqual(
                [(item.fecha, item.tipo_hora, item.cantidad) for item in concepts],
                [
                    (date(2026, 8, 20), "COMIDA", Decimal("1.00")),
                    (date(2026, 8, 20), "MERIENDA", Decimal("2.00")),
                    (date(2026, 8, 21), "MERIENDA", Decimal("1.00")),
                ],
            )
            self.assertTrue(all(item.tipo_dia == "HABIL" for item in concepts))
            selected_hour = db.query(HoraExtra).filter(
                HoraExtra.fecha == date(2026, 8, 20),
                HoraExtra.tipo_registro == "HORAS",
            ).one()
            expanded = expandir_ids_con_jornadas_pendientes([selected_hour.id], db)
            self.assertEqual(len(expanded), 4)
            approved_meal = HoraExtra(
                usuario_id=user.id, fecha=date(2026, 8, 20),
                cantidad=Decimal("1"), tipo_dia="TODOS", tipo_hora="COMIDA",
                tipo_registro="OTRAS", estado="APROBADA",
            )
            db.add(approved_meal)
            for item in db.query(HoraExtra).filter(
                HoraExtra.tipo_registro == "HORAS",
                HoraExtra.estado == "PENDIENTE",
            ):
                db.delete(item)
            db.flush()
            recalcular_conceptos_jornada_pendiente(user.id, date(2026, 8, 20), db)
            recalcular_conceptos_jornada_pendiente(user.id, date(2026, 8, 21), db)
            db.flush()
            self.assertEqual(db.query(HoraExtra).filter(
                HoraExtra.tipo_registro == "OTRAS",
                HoraExtra.estado == "PENDIENTE",
            ).count(), 0)
            self.assertEqual(db.query(HoraExtra).filter(
                HoraExtra.id == approved_meal.id,
                HoraExtra.estado == "APROBADA",
            ).count(), 1)

    def test_same_day_and_exact_midnight_remain_one_segment(self):
        fecha = date(2026, 8, 6)
        self.assertEqual(
            dividir_carga_en_fechas(fecha, time(18, 0), time(21, 0)),
            [(fecha, time(18, 0), time(21, 0))],
        )
        self.assertEqual(
            dividir_carga_en_fechas(fecha, time(22, 0), time(0, 0)),
            [(fecha, time(22, 0), time(0, 0))],
        )

    def test_equal_times_are_rejected(self):
        with self.assertRaises(CalculoHorasError):
            dividir_carga_en_fechas(
                date(2026, 8, 6), time(0, 0), time(0, 0)
            )


if __name__ == "__main__":
    unittest.main()
