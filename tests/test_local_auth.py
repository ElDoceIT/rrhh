import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database.models import Usuario, UsuarioRol
from app.services.local_auth import (
    authenticate_local_user,
    is_local_username,
    seed_local_admin,
)


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
            original_role = original.id_rol

            self.assertFalse(seed_local_admin(db))
            self.assertEqual(db.query(Usuario).count(), 1)
            stored = db.query(Usuario).one()
            self.assertEqual(stored.hashed_password, original_hash)
            self.assertEqual(stored.id_rol, original_role)
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


if __name__ == "__main__":
    unittest.main()
