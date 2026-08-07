import os
import ssl
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from ldap3 import ALL, BASE, Connection, Server, Tls
from ldap3.utils.conv import escape_filter_chars

load_dotenv()


@dataclass
class ADConfig:
    server_ip: str
    port: int
    use_ssl: bool
    validate_cert: bool
    bind_user: str
    bind_password: str
    user_base_dn: str
    groups_base_dn: str
    login_attr: str
    group_name_prefix: str


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


def load_ad_config() -> ADConfig | None:
    server_ip = os.getenv("AD_SERVER_IP", "").strip()
    bind_user = os.getenv("AD_BIND_USER", "").strip()
    bind_password = os.getenv("AD_BIND_PASSWORD", "").strip()
    user_base_dn = os.getenv("AD_BASE_DN", "").strip()
    groups_base_dn = os.getenv("AD_GROUPS_BASE_DN", "").strip() or user_base_dn

    if not all([server_ip, bind_user, bind_password, user_base_dn]):
        return None

    return ADConfig(
        server_ip=server_ip,
        port=int(os.getenv("AD_SERVER_PORT", "636")),
        use_ssl=_as_bool(os.getenv("AD_USE_SSL"), default=True),
        validate_cert=_as_bool(os.getenv("AD_TLS_VALIDATE_CERT"), default=False),
        bind_user=bind_user,
        bind_password=bind_password,
        user_base_dn=user_base_dn,
        groups_base_dn=groups_base_dn,
        login_attr=os.getenv("AD_LOGIN_ATTR", "sAMAccountName").strip() or "sAMAccountName",
        group_name_prefix=os.getenv("AD_GROUP_NAME_PREFIX", "").strip(),
    )


def _normalize_username(username: str) -> str:
    base = username.strip()
    if "@" in base:
        return base.split("@", 1)[0]
    if "\\" in base:
        return base.split("\\", 1)[1]
    return base


def _server_from_cfg(cfg: ADConfig) -> Server:
    tls_cfg = Tls(validate=ssl.CERT_REQUIRED if cfg.validate_cert else ssl.CERT_NONE)
    return Server(cfg.server_ip, port=cfg.port, use_ssl=cfg.use_ssl, get_info=ALL, tls=tls_cfg)


def _service_connection(cfg: ADConfig) -> Connection:
    return Connection(
        _server_from_cfg(cfg),
        user=cfg.bind_user,
        password=cfg.bind_password,
        auto_bind=True
    )


def authenticate_user(username: str, password: str) -> bool:
    cfg = load_ad_config()
    if not cfg:
        return False

    service_conn = None
    user_conn = None
    try:
        service_conn = _service_connection(cfg)
        login_value = escape_filter_chars(_normalize_username(username))
        service_conn.search(
            search_base=cfg.user_base_dn,
            search_filter=f"(&(objectClass=user)({cfg.login_attr}={login_value}))",
            attributes=["distinguishedName"],
            size_limit=1,
        )
        if not service_conn.entries:
            return False

        user_dn = str(service_conn.entries[0].entry_dn)
        user_conn = Connection(_server_from_cfg(cfg), user=user_dn, password=password, auto_bind=True)
        return user_conn.bound
    except Exception as e:
        print(f"[ad_auth] Error autenticando en AD: {e}")
        return False
    finally:
        if user_conn:
            user_conn.unbind()
        if service_conn:
            service_conn.unbind()


def list_groups() -> list[dict[str, str]]:
    cfg = load_ad_config()
    if not cfg:
        return []

    conn = None
    try:
        conn = _service_connection(cfg)
        search_filter = "(objectClass=group)"
        if cfg.group_name_prefix:
            safe_prefix = escape_filter_chars(cfg.group_name_prefix)
            search_filter = f"(&(objectClass=group)(cn={safe_prefix}*))"
        conn.search(
            search_base=cfg.groups_base_dn,
            search_filter=search_filter,
            attributes=["cn", "distinguishedName"],
        )
        groups: list[dict[str, str]] = []
        for entry in conn.entries:
            data = entry.entry_attributes_as_dict
            dn = str(data.get("distinguishedName", [""])[0] if isinstance(data.get("distinguishedName"), list) else data.get("distinguishedName", ""))
            cn_value = data.get("cn")
            if isinstance(cn_value, list):
                cn = str(cn_value[0]) if cn_value else dn
            else:
                cn = str(cn_value or dn)
            if dn:
                groups.append({"cn": cn, "dn": dn})
        groups.sort(key=lambda g: g["cn"].lower())
        return groups
    except Exception as e:
        print(f"[ad_sync] Error listando grupos AD: {e}")
        return []
    finally:
        if conn:
            conn.unbind()


def list_group_members(group_dn: str) -> list[dict[str, Any]]:
    cfg = load_ad_config()
    if not cfg:
        return []

    conn = None
    try:
        conn = _service_connection(cfg)
        safe_group_dn = group_dn.strip()
        if not safe_group_dn:
            return []

        conn.search(
            search_base=safe_group_dn,
            search_filter="(objectClass=group)",
            attributes=["member"],
            search_scope=BASE
        )
        if not conn.entries:
            return []

        group_attrs = conn.entries[0].entry_attributes_as_dict
        members = group_attrs.get("member", [])
        if not isinstance(members, list):
            members = [members]

        usuarios: list[dict[str, Any]] = []
        for member_dn in members:
            member_dn = str(member_dn).strip()
            if not member_dn:
                continue
            conn.search(
                search_base=member_dn,
                search_filter="(objectClass=user)",
                attributes=["sAMAccountName", "givenName", "sn", "mail", "userPrincipalName"],
                search_scope=BASE,
                size_limit=1,
            )
            if not conn.entries:
                continue
            attrs = conn.entries[0].entry_attributes_as_dict
            sam = attrs.get("sAMAccountName")
            if isinstance(sam, list):
                username = str(sam[0]) if sam else ""
            else:
                username = str(sam or "")
            if not username:
                continue

            given_name = attrs.get("givenName")
            sn = attrs.get("sn")
            mail = attrs.get("mail")
            upn = attrs.get("userPrincipalName")

            usuarios.append({
                "username": username,
                "nombre": (given_name[0] if isinstance(given_name, list) and given_name else given_name) or "",
                "apellido": (sn[0] if isinstance(sn, list) and sn else sn) or "",
                "email": (mail[0] if isinstance(mail, list) and mail else mail) or (
                    (upn[0] if isinstance(upn, list) and upn else upn) or ""
                ),
                "dn": member_dn,
            })

        return usuarios
    except Exception as e:
        print(f"[ad_sync] Error listando miembros de grupo AD: {e}")
        return []
    finally:
        if conn:
            conn.unbind()
