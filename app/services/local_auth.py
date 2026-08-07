import logging
import os

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.database.models import Usuario, UsuarioRol


logger = logging.getLogger(__name__)


def normalize_username(username: str) -> str:
    return username.strip().lower()


def local_usernames() -> set[str]:
    configured = os.getenv("AUTH_LOCAL_USERS", "admin,root")
    return {
        normalized
        for item in configured.split(",")
        if (normalized := normalize_username(item))
    }


def is_local_username(username: str) -> bool:
    return normalize_username(username) in local_usernames()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def find_user(db: Session, username: str) -> Usuario | None:
    normalized = normalize_username(username)
    if not normalized:
        return None
    return db.scalar(
        select(Usuario)
        .options(selectinload(Usuario.roles))
        .where(func.lower(Usuario.username) == normalized)
    )


def authenticate_local_user(db: Session, username: str, password: str) -> Usuario | None:
    if not is_local_username(username) or not password:
        return None
    user = find_user(db, username)
    if user is None or not user.status or not user.hashed_password:
        return None
    try:
        valid = bcrypt.checkpw(
            password.encode("utf-8"),
            user.hashed_password.encode("utf-8"),
        )
    except (TypeError, ValueError):
        logger.warning("El hash del usuario local %s no es válido.", normalize_username(username))
        return None
    return user if valid else None


def session_user(user: Usuario, source: str) -> dict:
    assignments = [
        {"id": item.id_rol, "role": item.rol, "profile": item.perfil}
        for item in sorted(user.roles, key=lambda item: (item.rol, item.perfil))
    ]
    active = assignments[0] if assignments else None
    return {
        "id": user.id,
        "username": user.username,
        "display_name": f"{user.nombre} {user.apellido}".strip() or user.username,
        "email": user.correo,
        "source": source,
        "assignments": assignments,
        "active_assignment_id": active["id"] if active else None,
        "role": active["role"] if active else None,
        "profile": active["profile"] if active else None,
    }


def seed_local_admin(db: Session) -> bool:
    password = os.getenv("SEED_ADMIN_PASSWORD")
    if not password:
        logger.warning(
            "SEED_ADMIN_PASSWORD no está configurada; no se creará el administrador local."
        )
        return False

    username = normalize_username(os.getenv("SEED_ADMIN_USERNAME", "admin"))
    if not username:
        logger.warning("SEED_ADMIN_USERNAME está vacío; no se creará el administrador local.")
        return False
    if username not in local_usernames():
        logger.warning(
            "El seed admin %s no figura en AUTH_LOCAL_USERS; no se creará.", username
        )
        return False
    if find_user(db, username) is not None:
        logger.info("El administrador local %s ya existe; no se modificará.", username)
        return False

    user = Usuario(
        nombre=os.getenv("SEED_ADMIN_NOMBRE", "Admin").strip() or "Admin",
        apellido=os.getenv("SEED_ADMIN_APELLIDO", "Local").strip() or "Local",
        correo=os.getenv("SEED_ADMIN_EMAIL", "admin@local.invalid").strip() or None,
        username=username,
        hashed_password=hash_password(password),
        origen="LOCAL",
        status=True,
    )
    db.add(user)
    db.flush()
    db.add(UsuarioRol(usuario_id=user.id, rol="ADMIN", perfil="JEFE"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Otro worker pudo haber creado el mismo usuario durante el arranque.
        if find_user(db, username) is not None:
            logger.info("El administrador local %s ya fue creado por otro proceso.", username)
            return False
        raise
    logger.info("Administrador local %s creado correctamente.", username)
    return True


def initialize_seed_admin(session_factory) -> None:
    try:
        with session_factory() as db:
            seed_local_admin(db)
    except SQLAlchemyError:
        logger.exception("No se pudo inicializar el administrador local de emergencia.")
