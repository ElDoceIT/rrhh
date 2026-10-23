import os
import ssl
from dataclasses import dataclass

from ldap3 import ALL, BASE, SIMPLE, Connection, Server, Tls
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars


class ActiveDirectoryAuthError(Exception):
    pass


@dataclass(frozen=True)
class ActiveDirectoryUser:
    username: str
    display_name: str
    email: str | None
    distinguished_name: str


@dataclass(frozen=True)
class ActiveDirectoryGroupUser:
    username: str
    display_name: str
    first_name: str
    last_name: str
    email: str | None


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ActiveDirectoryAuthError(f"Falta configurar {name}.")
    return value


def _server() -> Server:
    validate = ssl.CERT_REQUIRED if _env_bool("AD_TLS_VALIDATE_CERT") else ssl.CERT_NONE
    tls = Tls(validate=validate)
    return Server(
        _required_env("AD_SERVER_IP"),
        port=int(os.getenv("AD_SERVER_PORT", "389")),
        use_ssl=_env_bool("AD_USE_SSL"),
        tls=tls,
        get_info=ALL,
        connect_timeout=int(os.getenv("AD_CONNECT_TIMEOUT", "5")),
    )


def _bind_user() -> str:
    bind_user = _required_env("AD_BIND_USER")
    domain = os.getenv("AD_DOMAIN")
    if "\\" not in bind_user and "@" not in bind_user and domain:
        return f"{bind_user}@{domain}"
    return bind_user


def _domain_root_dn(dn: str) -> str:
    """Extrae la raíz del dominio (componentes DC=...) de un Distinguished Name."""
    parts = [p.strip() for p in dn.split(",") if p.strip()]
    dc_parts = [p for p in parts if p.upper().startswith("DC=")]
    if dc_parts:
        return ",".join(dc_parts)
    domain = os.getenv("AD_DOMAIN")
    if domain:
        return ",".join(f"DC={part}" for part in domain.split(".") if part)
    return dn


def _configured_group_dns(connection: Connection) -> list[str]:
    """
    Obtiene los Distinguished Names (DNs) de los grupos configurados en AD_GROUP_NAME.
    Permite uno o varios grupos separados por comas o punto y coma.
    """
    raw_group_name = _required_env("AD_GROUP_NAME")
    base_dn = _required_env("AD_BASE_DN")
    groups_base_dn = os.getenv("AD_GROUPS_BASE_DN") or _domain_root_dn(base_dn)

    group_names = [g.strip() for g in raw_group_name.replace(";", ",").split(",") if g.strip()]
    if not group_names:
        raise ActiveDirectoryAuthError("Falta configurar AD_GROUP_NAME.")

    found_dns: list[str] = []
    for group_name in group_names:
        escaped_group = escape_filter_chars(group_name)
        connection.search(
            groups_base_dn,
            f"(&(objectClass=group)(cn={escaped_group}))",
            attributes=["distinguishedName"],
            size_limit=1,
        )
        if connection.entries:
            found_dns.append(connection.entries[0].entry_dn)
        else:
            # Reintento sobre base_dn directo por si groups_base_dn tenía otro alcance
            if groups_base_dn != base_dn:
                connection.search(
                    base_dn,
                    f"(&(objectClass=group)(cn={escaped_group}))",
                    attributes=["distinguishedName"],
                    size_limit=1,
                )
                if connection.entries:
                    found_dns.append(connection.entries[0].entry_dn)
                    continue
            raise ActiveDirectoryAuthError(f"No se encontró el grupo '{group_name}' en Active Directory.")

    return found_dns


def _configured_group_dn(connection: Connection) -> str:
    """Mantiene compatibilidad hacia atrás devolviendo el primer grupo configurado."""
    dns = _configured_group_dns(connection)
    return dns[0]


def _collect_nested_group_dns(
    connection: Connection, root_group_dns: list[str], search_base: str
) -> set[str]:
    """
    Descubre recursivamente todos los subgrupos anidados (por ejemplo, si IT está dentro de Comercial o RRHH).
    Maneja ciclos y busca tanto por atributo 'memberOf' como por el atributo 'member' del grupo padre.
    """
    all_group_dns: set[str] = set(root_group_dns)
    queue: list[str] = list(root_group_dns)

    while queue:
        current_dn = queue.pop(0)
        escaped_current_dn = escape_filter_chars(current_dn)

        # 1. Buscar grupos cuyo memberOf sea el grupo actual
        connection.search(
            search_base,
            f"(&(objectClass=group)(memberOf={escaped_current_dn}))",
            attributes=["distinguishedName"],
        )
        for entry in connection.entries:
            entry_dn = entry.entry_dn
            if entry_dn and entry_dn not in all_group_dns:
                all_group_dns.add(entry_dn)
                queue.append(entry_dn)

        # 2. Leer miembros directos del grupo actual para ver si alguno es un subgrupo
        connection.search(
            current_dn,
            "(objectClass=group)",
            search_scope=BASE,
            attributes=["member"],
        )
        if connection.entries:
            raw_members = connection.entries[0].member.values if hasattr(connection.entries[0], "member") else []
            for member_val in raw_members:
                member_dn = str(member_val).strip()
                if member_dn and member_dn not in all_group_dns:
                    # Chequear si este miembro es un grupo
                    connection.search(
                        member_dn,
                        "(objectClass=group)",
                        search_scope=BASE,
                        attributes=["distinguishedName"],
                    )
                    if connection.entries:
                        all_group_dns.add(member_dn)
                        queue.append(member_dn)

    return all_group_dns


def _build_member_of_filter(root_group_dns: list[str], all_group_dns: set[str]) -> str:
    """Construye la cláusula LDAP de pertenencia combinando regla en cadena y memberOf directo."""
    clauses: list[str] = []
    # Regla en cadena nativa de AD para los grupos raíz
    for r_dn in root_group_dns:
        clauses.append(f"(memberOf:1.2.840.113556.1.4.1941:={escape_filter_chars(r_dn)})")
    # Pertenencia directa a cualquiera de los grupos (padres o subgrupos anidados como IT)
    for g_dn in all_group_dns:
        clauses.append(f"(memberOf={escape_filter_chars(g_dn)})")

    if len(clauses) == 1:
        return clauses[0]
    return f"(|{''.join(clauses)})"


def list_ad_group_users() -> list[ActiveDirectoryGroupUser]:
    login_attr = os.getenv("AD_LOGIN_ATTR", "sAMAccountName")
    base_dn = _required_env("AD_BASE_DN")
    # Usamos la raíz del dominio para que no queden excluidos usuarios de otras OUs
    users_search_base = _domain_root_dn(base_dn)

    try:
        with Connection(
            _server(),
            user=_bind_user(),
            password=_required_env("AD_BIND_PASSWORD"),
            authentication=SIMPLE,
            auto_bind=True,
        ) as service_connection:
            root_group_dns = _configured_group_dns(service_connection)
            all_group_dns = _collect_nested_group_dns(service_connection, root_group_dns, users_search_base)

            membership_filter = _build_member_of_filter(root_group_dns, all_group_dns)
            service_connection.search(
                users_search_base,
                (
                    "(&"
                    "(objectClass=user)"
                    "(!(objectClass=computer))"
                    f"{membership_filter}"
                    ")"
                ),
                attributes=[login_attr, "displayName", "givenName", "sn", "mail"],
            )

            seen_usernames: set[str] = set()
            users: list[ActiveDirectoryGroupUser] = []

            for entry in service_connection.entries:
                username = str(entry[login_attr] or "").strip()
                if not username or username.lower() in seen_usernames:
                    continue
                seen_usernames.add(username.lower())

                display_name = str(entry.displayName or "").strip()
                if not display_name:
                    display_name = " ".join(
                        part
                        for part in (
                            str(entry.givenName or "").strip(),
                            str(entry.sn or "").strip(),
                        )
                        if part
                    )
                users.append(ActiveDirectoryGroupUser(
                    username=username,
                    display_name=display_name or username,
                    first_name=str(entry.givenName or "").strip() or display_name or username,
                    last_name=str(entry.sn or "").strip() or "-",
                    email=str(entry.mail or "").strip() or None,
                ))

            return sorted(users, key=lambda user: (user.display_name.lower(), user.username.lower()))
    except ActiveDirectoryAuthError:
        raise
    except LDAPException as error:
        raise ActiveDirectoryAuthError(
            "No se pudo consultar el grupo de Active Directory."
        ) from error


def authenticate_ad_user(username: str, password: str) -> ActiveDirectoryUser:
    username = username.strip()
    if not username or not password:
        raise ActiveDirectoryAuthError("Ingresá usuario y contraseña.")

    login_attr = os.getenv("AD_LOGIN_ATTR", "sAMAccountName")
    base_dn = _required_env("AD_BASE_DN")
    users_search_base = _domain_root_dn(base_dn)

    try:
        with Connection(
            _server(),
            user=_bind_user(),
            password=_required_env("AD_BIND_PASSWORD"),
            authentication=SIMPLE,
            auto_bind=True,
        ) as service_connection:
            root_group_dns = _configured_group_dns(service_connection)
            all_group_dns = _collect_nested_group_dns(service_connection, root_group_dns, users_search_base)

            escaped_username = escape_filter_chars(username)
            membership_filter = _build_member_of_filter(root_group_dns, all_group_dns)

            service_connection.search(
                users_search_base,
                (
                    "(&"
                    "(objectClass=user)"
                    "(!(objectClass=computer))"
                    f"({login_attr}={escaped_username})"
                    f"{membership_filter}"
                    ")"
                ),
                attributes=[login_attr, "displayName", "givenName", "sn", "mail"],
                size_limit=1,
            )
            if not service_connection.entries:
                raise ActiveDirectoryAuthError("El usuario no está habilitado para esta aplicación.")

            entry = service_connection.entries[0]
            user_dn = entry.entry_dn

        with Connection(
            _server(),
            user=user_dn,
            password=password,
            authentication=SIMPLE,
            auto_bind=True,
        ):
            display_name = str(entry.displayName or "").strip()
            if not display_name:
                display_name = " ".join(
                    part for part in [str(entry.givenName or "").strip(), str(entry.sn or "").strip()]
                    if part
                )
            return ActiveDirectoryUser(
                username=username,
                display_name=display_name or username,
                email=str(entry.mail or "").strip() or None,
                distinguished_name=user_dn,
            )
    except ActiveDirectoryAuthError:
        raise
    except LDAPException as error:
        raise ActiveDirectoryAuthError("No se pudo validar el usuario contra Active Directory.") from error
