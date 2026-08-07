import os
from urllib.parse import quote

import bcrypt
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database import get_connection
from routes.auth import get_session_context, session_template_context
from services.ad_sync import list_group_members, list_groups, load_ad_config

router = APIRouter()
templates = Jinja2Templates(directory="templates")

VALID_ROLES = {"admin", "operador", "vendedor"}
ROLE_PRIORITY = {
    "admin": 3,
    "operador": 2,
    "vendedor": 1,
}


def _local_users() -> set[str]:
    users = os.getenv("AUTH_LOCAL_USERS", "admin,root")
    return {u.strip().lower() for u in users.split(",") if u.strip()}


def _ensure_mapping_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ad_group_role_map (
            id INT NOT NULL AUTO_INCREMENT,
            group_dn VARCHAR(512) NOT NULL,
            group_name VARCHAR(255) NOT NULL,
            rol VARCHAR(50) NOT NULL,
            activo TINYINT(1) NOT NULL DEFAULT 1,
            creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uq_ad_group_dn (group_dn)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """
    )


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


def _read_mappings(cursor):
    _ensure_mapping_table(cursor)
    cursor.execute(
        """
        SELECT id,
               group_dn,
               group_name,
               CASE WHEN rol = 'vendedor-j' THEN 'vendedor' ELSE rol END AS rol,
               activo
        FROM ad_group_role_map
        ORDER BY group_name ASC
        """
    )
    return cursor.fetchall()


def _render_page(
    request: Request,
    flash: str = "",
    flash_kind: str = "is-info",
    selected_group_dn: str = "",
    show_inactive: bool = False,
):
    user_ctx = get_session_context(request)
    if not user_ctx:
        return RedirectResponse(url="/login", status_code=303)
    if user_ctx["rol"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    conn = get_connection()
    if conn is None:
        return templates.TemplateResponse(
            "ad_sync.html",
            {
                "request": request,
                **session_template_context(user_ctx),
                "mappings": [],
                "groups": [],
                "flash": "No se pudo conectar a la base de datos.",
                "flash_kind": "is-danger",
                "ad_config_ok": load_ad_config() is not None,
                "selected_group_dn": selected_group_dn,
                "selected_group_name": "",
                "selected_group_members": [],
                "show_inactive": show_inactive,
            },
        )
    cursor = conn.cursor(dictionary=True)
    all_mappings = _read_mappings(cursor)
    cursor.close()
    conn.close()

    if show_inactive:
        mappings = all_mappings
    else:
        mappings = [m for m in all_mappings if int(m.get("activo", 0)) == 1]

    ad_config_ok = load_ad_config() is not None
    groups = list_groups()
    selected_group_members = []
    selected_group_name = ""

    if selected_group_dn and ad_config_ok:
        selected_group_members = list_group_members(selected_group_dn)
        for mapping in all_mappings:
            if mapping["group_dn"] == selected_group_dn:
                selected_group_name = mapping["group_name"]
                break
        if not selected_group_name:
            for group in groups:
                if group["dn"] == selected_group_dn:
                    selected_group_name = group["cn"]
                    break

    return templates.TemplateResponse(
        "ad_sync.html",
        {
            "request": request,
            **session_template_context(user_ctx),
            "mappings": mappings,
            "groups": groups,
            "flash": flash,
            "flash_kind": flash_kind,
            "ad_config_ok": ad_config_ok,
            "selected_group_dn": selected_group_dn,
            "selected_group_name": selected_group_name,
            "selected_group_members": selected_group_members,
            "show_inactive": show_inactive,
        },
    )


@router.get("/admin/ad-sync", response_class=HTMLResponse)
def ad_sync_view(request: Request, group_dn: str = "", show_inactive: str = "0"):
    return _render_page(
        request,
        selected_group_dn=group_dn.strip(),
        show_inactive=_as_bool(show_inactive, default=False),
    )


@router.post("/admin/ad-sync/mapping")
def save_mapping(
    request: Request,
    group_dn: str = Form(...),
    group_name: str = Form(...),
    rol: str = Form(...),
    activo: str | None = Form(None),
):
    user_ctx = get_session_context(request)
    if not user_ctx:
        return RedirectResponse(url="/login", status_code=303)
    if user_ctx["rol"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    role_value = rol.strip().lower()
    if role_value not in VALID_ROLES:
        return _render_page(request, "Rol inválido para mapeo.", "is-danger")

    conn = get_connection()
    if conn is None:
        return _render_page(request, "No se pudo conectar a la base de datos.", "is-danger")
    cursor = conn.cursor()
    _ensure_mapping_table(cursor)
    cursor.execute(
        """
        INSERT INTO ad_group_role_map (group_dn, group_name, rol, activo)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            group_name = VALUES(group_name),
            rol = VALUES(rol),
            activo = VALUES(activo)
        """,
        (group_dn.strip(), group_name.strip(), role_value, 1 if activo else 0),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(url=f"/admin/ad-sync?group_dn={quote(group_dn.strip())}", status_code=303)


@router.post("/admin/ad-sync/mapping/{mapping_id}/update")
def update_mapping(
    request: Request,
    mapping_id: int,
    rol: str = Form(...),
    activo: str | None = Form(None),
    return_group_dn: str = Form(""),
    return_show_inactive: str = Form("0"),
):
    user_ctx = get_session_context(request)
    if not user_ctx:
        return RedirectResponse(url="/login", status_code=303)
    if user_ctx["rol"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    role_value = rol.strip().lower()
    if role_value not in VALID_ROLES:
        return _render_page(request, "Rol inválido para mapeo.", "is-danger")

    conn = get_connection()
    if conn is None:
        return _render_page(request, "No se pudo conectar a la base de datos.", "is-danger")
    cursor = conn.cursor()
    _ensure_mapping_table(cursor)
    cursor.execute(
        """
        UPDATE ad_group_role_map
        SET rol = %s, activo = %s
        WHERE id = %s
        """,
        (role_value, 1 if activo else 0, mapping_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
    redirect_dn = return_group_dn.strip()
    show_inactive_value = "1" if _as_bool(return_show_inactive, default=False) else "0"
    if redirect_dn:
        return RedirectResponse(
            url=f"/admin/ad-sync?group_dn={quote(redirect_dn)}&show_inactive={show_inactive_value}",
            status_code=303,
        )
    return RedirectResponse(url=f"/admin/ad-sync?show_inactive={show_inactive_value}", status_code=303)


@router.post("/admin/ad-sync/mapping/{mapping_id}/toggle")
def toggle_mapping(
    request: Request,
    mapping_id: int,
    return_group_dn: str = Form(""),
    return_show_inactive: str = Form("0"),
):
    user_ctx = get_session_context(request)
    if not user_ctx:
        return RedirectResponse(url="/login", status_code=303)
    if user_ctx["rol"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    conn = get_connection()
    if conn is None:
        return _render_page(request, "No se pudo conectar a la base de datos.", "is-danger")
    cursor = conn.cursor()
    _ensure_mapping_table(cursor)
    cursor.execute(
        """
        UPDATE ad_group_role_map
        SET activo = CASE WHEN activo = 1 THEN 0 ELSE 1 END
        WHERE id = %s
        """,
        (mapping_id,),
    )
    conn.commit()
    cursor.close()
    conn.close()
    redirect_dn = return_group_dn.strip()
    show_inactive_value = "1" if _as_bool(return_show_inactive, default=False) else "0"
    if redirect_dn:
        return RedirectResponse(
            url=f"/admin/ad-sync?group_dn={quote(redirect_dn)}&show_inactive={show_inactive_value}",
            status_code=303,
        )
    return RedirectResponse(url=f"/admin/ad-sync?show_inactive={show_inactive_value}", status_code=303)


@router.post("/admin/ad-sync/run")
def run_sync(request: Request):
    user_ctx = get_session_context(request)
    if not user_ctx:
        return RedirectResponse(url="/login", status_code=303)
    if user_ctx["rol"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    if load_ad_config() is None:
        return _render_page(request, "Falta configurar variables de AD en .env.", "is-danger")

    conn = get_connection()
    if conn is None:
        return _render_page(request, "No se pudo conectar a la base de datos.", "is-danger")
    cursor = conn.cursor(dictionary=True)
    mappings = _read_mappings(cursor)
    active_mappings = [m for m in mappings if int(m.get("activo", 0)) == 1]
    cursor.close()

    if not active_mappings:
        conn.close()
        return _render_page(request, "No hay grupos activos para sincronizar.", "is-warning")

    local_users = _local_users()
    users_merged: dict[str, dict] = {}
    role_collisions = 0

    for mapping in active_mappings:
        members = list_group_members(mapping["group_dn"])
        for member in members:
            username = str(member.get("username", "")).strip()
            if not username:
                continue
            if username.lower() in local_users:
                continue

            incoming_role = mapping["rol"]
            current = users_merged.get(username)
            if not current:
                users_merged[username] = {
                    "username": username,
                    "nombre": str(member.get("nombre", "")).strip(),
                    "apellido": str(member.get("apellido", "")).strip(),
                    "email": str(member.get("email", "")).strip(),
                    "rol": incoming_role,
                }
                continue

            if ROLE_PRIORITY.get(incoming_role, 0) > ROLE_PRIORITY.get(current["rol"], 0):
                current["rol"] = incoming_role
                role_collisions += 1

            if not current["nombre"] and member.get("nombre"):
                current["nombre"] = str(member["nombre"]).strip()
            if not current["apellido"] and member.get("apellido"):
                current["apellido"] = str(member["apellido"]).strip()
            if not current["email"] and member.get("email"):
                current["email"] = str(member["email"]).strip()

    cursor = conn.cursor(dictionary=True)
    inserted = 0
    updated = 0
    skipped = 0

    for user in users_merged.values():
        cursor.execute("SELECT id FROM usuarios WHERE username = %s", (user["username"],))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE usuarios
                SET nombre = %s,
                    apellido = %s,
                    email = %s,
                    rol = %s
                WHERE id = %s
                """,
                (
                    user["nombre"] or user["username"],
                    user["apellido"] or "-",
                    user["email"] or f"{user['username']}@local.invalid",
                    user["rol"],
                    existing["id"],
                ),
            )
            updated += 1
            continue

        random_secret = os.urandom(24).hex()
        random_hash = bcrypt.hashpw(random_secret.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            cursor.execute(
                """
                INSERT INTO usuarios (nombre, apellido, username, email, password_hash, rol)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user["nombre"] or user["username"],
                    user["apellido"] or "-",
                    user["username"],
                    user["email"] or f"{user['username']}@local.invalid",
                    random_hash,
                    user["rol"],
                ),
            )
            inserted += 1
        except Exception:
            skipped += 1

    conn.commit()
    cursor.close()
    conn.close()

    msg = (
        f"Sync AD completado. Insertados: {inserted}, actualizados: {updated}, "
        f"omitidos: {skipped}, conflictos de rol resueltos por prioridad: {role_collisions}."
    )
    return _render_page(request, msg, "is-success")
