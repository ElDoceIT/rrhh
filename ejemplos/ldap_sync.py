from dataclasses import dataclass

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.services.ldap import LDAPConnection
from app.services.ldap_auth import LDAPAuthService


@dataclass
class LDAPSyncResult:
    created: int = 0
    updated: int = 0
    activated: int = 0
    deactivated: int = 0
    admin_roles_synced: int = 0
    skipped_email_conflicts: int = 0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _normalize_username(value: object) -> str:
    return str(value or "").strip().lower()


def _normalize_email(value: object, username: str) -> str:
    email = str(value or "").strip().lower()
    return email or f"{username}@{settings.ldap_domain}".lower()


def _split_display_name(member: dict) -> tuple[str, str]:
    given_name = str(member.get("givenName") or "").strip()
    surname = str(member.get("sn") or "").strip()
    if given_name or surname:
        return given_name or str(member.get("username") or "").strip(), surname

    display = str(member.get("displayName") or member.get("nombre") or member.get("username") or "").strip()
    name_parts = display.split(" ", 1)
    return name_parts[0], name_parts[1] if len(name_parts) > 1 else ""


def _find_existing_ad_user(db: Session, username: str, email: str) -> User | None:
    fallback_email = f"{username}@{settings.ldap_domain}".lower()
    return (
        db.query(User)
        .filter(func.lower(User.username) == username)
        .first()
    ) or (
        db.query(User)
        .filter(or_(func.lower(User.correo) == email, func.lower(User.correo) == fallback_email))
        .first()
    )


def _apply_member_to_user(db: Session, member: dict) -> tuple[User | None, str]:
    username = _normalize_username(member.get("username"))
    if not username:
        return None, "skipped"

    email = _normalize_email(member.get("mail"), username)
    nombre, apellido = _split_display_name(member)
    user = _find_existing_ad_user(db, username, email)

    if user is None:
        duplicate_email = db.query(User).filter(func.lower(User.correo) == email).first()
        if duplicate_email is not None:
            return None, "email_conflict"
        user = User(
            username=username,
            nombre=nombre,
            apellido=apellido,
            correo=email,
            hashed_password="LDAP_USER",
            origen="AD",
            status=1,
        )
        db.add(user)
        return user, "created"

    duplicate_email = (
        db.query(User)
        .filter(func.lower(User.correo) == email, User.id != int(user.id))
        .first()
    )
    if duplicate_email is not None:
        return None, "email_conflict"

    action = "activated" if int(user.status or 0) == 0 else "updated"
    user.username = username
    user.nombre = nombre
    user.apellido = apellido
    user.correo = email
    user.origen = "AD"
    user.status = 1
    return user, action


def apply_ldap_members_to_db(db: Session, app_members: list[dict], admin_members: list[dict] | None = None) -> LDAPSyncResult:
    result = LDAPSyncResult()
    admin_members = admin_members or []
    all_members_by_username: dict[str, dict] = {}

    for member in [*app_members, *admin_members]:
        username = _normalize_username(member.get("username"))
        if username:
            all_members_by_username[username] = member

    for member in all_members_by_username.values():
        user, action = _apply_member_to_user(db, member)
        if action == "email_conflict":
            result.skipped_email_conflicts += 1
            continue
        db.flush()

        if user is None:
            continue
        if action == "created":
            result.created += 1
        elif action == "activated":
            result.activated += 1
        elif action == "updated":
            result.updated += 1

    active_usernames = set(all_members_by_username)
    for user in db.query(User).filter(func.lower(func.coalesce(User.origen, "")) == "ad").all():
        if _normalize_username(user.username) not in active_usernames and int(user.status or 0) != 0:
            user.status = 0
            result.deactivated += 1

    admin_group_name = LDAPAuthService.get_admin_group_name()
    admin_usernames = {_normalize_username(member.get("username")) for member in admin_members}
    admin_users = (
        db.query(User)
        .filter(User.origen == "AD", User.status == 1)
        .all()
    )
    for user in admin_users:
        if _normalize_username(user.username) in admin_usernames:
            LDAPAuthService.ensure_admin_role_for_user(db, user, [admin_group_name])
            result.admin_roles_synced += 1

    db.commit()
    return result


def sync_ldap_users(db: Session) -> LDAPSyncResult:
    app_group_name = LDAPAuthService.get_app_group_name()
    admin_group_name = LDAPAuthService.get_admin_group_name()
    ldap_connection = LDAPConnection()

    try:
        if not ldap_connection.connect():
            return LDAPSyncResult(error=f"No se pudo conectar al AD ({settings.ldap_server_ip}:{settings.ldap_server_port})")

        try:
            app_members = ldap_connection.get_group_members(app_group_name)
            admin_members = ldap_connection.get_group_members(admin_group_name)
        finally:
            ldap_connection.disconnect()

        return apply_ldap_members_to_db(db, app_members, admin_members)
    except Exception as exc:
        db.rollback()
        return LDAPSyncResult(error=str(exc))


def format_ldap_sync_result(result: LDAPSyncResult) -> str:
    if result.error:
        return f"Error sincronizando LDAP: {result.error}"
    return (
        "LDAP sincronizado: "
        f"{result.created} creados, "
        f"{result.updated} actualizados, "
        f"{result.activated} reactivados, "
        f"{result.deactivated} desactivados, "
        f"{result.skipped_email_conflicts} omitidos por conflicto de correo"
    )
