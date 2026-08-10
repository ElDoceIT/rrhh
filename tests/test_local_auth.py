import os
import unittest
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app.database.connection import Base
from app.database.models import ReglaHora, Usuario, UsuarioRol
from app.services.local_auth import (
    authenticate_local_user,
    is_local_username,
    seed_local_admin,
    session_user,
)
from app.services.calculo_horas import (
    CalculoHorasError,
    calcular_horas_totales,
    calcular_resultado_horas_extra,
    calcular_resultado_otra_carga,
    calcular_resultado_reintegro,
    clasificar_tipo_dia,
    dividir_carga_en_fechas,
)
from app.services.access_catalog import CONVENIOS_DISPONIBLES, PERFILES_DISPONIBLES, ROLES_DISPONIBLES
from app.main import (
    ids_habilitados_para_confirmar,
    obtener_autorizador,
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

    def test_chief_can_only_load_users_from_active_role(self):
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
            _, terceros = usuarios_habilitados_para_carga(request, db, "otro")
            self.assertEqual([item.id for item in terceros], [empleado.id])
            self.assertEqual(ids_habilitados_para_confirmar(request, db), {empleado.id})
            actor, assignment, is_admin = obtener_autorizador(request, db)
            self.assertEqual(actor.id, jefe.id)
            self.assertEqual(assignment.rol, "COMERCIAL")
            self.assertFalse(is_admin)

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


class MidnightSplitTests(unittest.TestCase):
    def test_times_must_use_half_hour_intervals(self):
        with self.assertRaisesRegex(CalculoHorasError, "30 minutos"):
            calcular_resultado_horas_extra(
                1, date(2026, 8, 6), time(22, 15), time(23, 0), None
            )


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
            self.assertEqual(result.tipo_dia, "TODOS")
            self.assertEqual(result.cantidad, Decimal("8.00"))
            self.assertIsNone(result.hora_inicio)
            self.assertIsNone(result.horas_totales)

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
