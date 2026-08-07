import os
import re

import bcrypt
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_connection
from routes.auth import etiqueta_rol_usuario
router = APIRouter()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

VALID_ROLES = {"admin", "operador", "vendedor"}
VALID_PERFILES = {"usuario", "jefe"}


def _normalize_rol_perfil(rol: str, perfil: str):
    rol_value = (rol or "").strip().lower()
    perfil_value = (perfil or "usuario").strip().lower() or "usuario"
    if rol_value not in VALID_ROLES:
        rol_value = "vendedor"
    if perfil_value not in VALID_PERFILES:
        perfil_value = "usuario"
    return rol_value, perfil_value


def _local_users() -> set[str]:
    users = os.getenv("AUTH_LOCAL_USERS", "admin,root")
    return {u.strip().lower() for u in users.split(",") if u.strip()}


def _as_bool_int(value: str | None, default: int = 1) -> int:
    if value is None:
        return default
    return 1 if value.strip().lower() in {"1", "true", "yes", "on", "si", "sí"} else 0


def _username_from_email(email: str) -> str:
    base = (email or "").split("@", 1)[0].strip().lower()
    base = re.sub(r"[^a-z0-9._-]+", "", base)
    return base or "usuario"


def _unique_username(cursor, email: str) -> str:
    base = _username_from_email(email)
    candidate = base
    suffix = 2
    while True:
        cursor.execute("SELECT 1 FROM usuarios WHERE LOWER(username) = LOWER(%s) LIMIT 1", (candidate,))
        if cursor.fetchone() is None:
            return candidate
        candidate = f"{base}{suffix}"
        suffix += 1


def _random_password_hash() -> str:
    random_secret = os.urandom(24).hex()
    return bcrypt.hashpw(random_secret.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@router.get("/usuarios", response_class=HTMLResponse)
def vista_lista_usuarios(request: Request):
    user_session = request.cookies.get("session_user")
    rol = request.cookies.get("session_rol")

    # Seguridad: Solo admin ve la lista
    if not user_session or rol != "admin":
        return RedirectResponse(url="/", status_code=303)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, nombre, apellido, email, rol, perfil, activo FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()

    local_users = _local_users()
    for usuario in usuarios:
        username = str(usuario.get("username") or "").strip().lower()
        usuario["origen_auth"] = "Local" if username in local_users else "AD"
        usuario["rol_etiqueta"] = etiqueta_rol_usuario(usuario)

    return templates.TemplateResponse("usuarios_lista.html", {
        "request": request,
        "usuarios": usuarios,
        "usuario_actual": user_session,
        "rol_actual": rol,
        "perfil_actual": request.cookies.get("session_perfil", "usuario"),
        "rol_etiqueta_actual": "Administrador",
        "puede_exportar_actual": True,
        "puede_subir_sap_actual": True,
    })

@router.get("/usuarios/nuevo", response_class=HTMLResponse)
def vista_formulario_nuevo(request: Request):
    user_session = request.cookies.get("session_user")
    rol = request.cookies.get("session_rol")

    # Seguridad: Solo admin puede cargar nuevos
    if not user_session or rol != "admin":
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse("usuarios_nuevo.html", {
        "request": request,
        "usuario_actual": user_session,
        "rol_actual": rol,
        "perfil_actual": request.cookies.get("session_perfil", "usuario"),
        "rol_etiqueta_actual": "Administrador",
        "puede_exportar_actual": True,
        "puede_subir_sap_actual": True,
    })

@router.post("/usuarios/nuevo")
async def crear_usuario_post(request: Request):
    user_session = request.cookies.get("session_user")
    if not user_session:
        return RedirectResponse(url="/login", status_code=303)
    if request.cookies.get("session_rol") != "admin":
        return RedirectResponse(url="/", status_code=303)

    form = await request.form()
    nombre = str(form.get("nombre") or "").strip()
    apellido = str(form.get("apellido") or "").strip()
    email = str(form.get("email") or "").strip()
    rol = str(form.get("rol") or "").strip()
    perfil = str(form.get("perfil") or "usuario").strip()
    activo = str(form.get("activo")) if form.get("activo") is not None else None
    if not nombre or not apellido or not email or not rol:
        return RedirectResponse(url="/usuarios/nuevo", status_code=303)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        rol_value, perfil_value = _normalize_rol_perfil(rol, perfil)
        username = _unique_username(cursor, email)
        hashed_pw = _random_password_hash()
        activo_value = _as_bool_int(activo, default=0)

        sql = """
              INSERT INTO usuarios (nombre, apellido, username, email, password_hash, rol, perfil, activo)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        valores = (nombre, apellido, username, email, hashed_pw, rol_value, perfil_value, activo_value)

        cursor.execute(sql, valores)
        conn.commit()
        print(f"✅ Usuario {username} creado correctamente.")

    except Exception as e:
        print(f"❌ Error al insertar en DB: {e}")
    finally:
        conn.close()

    return RedirectResponse(url="/usuarios", status_code=303)


@router.get("/usuarios/editar/{usuario_id}")
def vista_editar_usuario(request: Request, usuario_id: int):
    user_session = request.cookies.get("session_user")
    rol = request.cookies.get("session_rol")

    if not user_session or rol != "admin":
        return RedirectResponse(url="/", status_code=303)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Buscamos los datos actuales del usuario
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    usuario = cursor.fetchone()

    cursor.close()
    conn.close()

    if not usuario:
        return RedirectResponse(url="/usuarios", status_code=303)

    return templates.TemplateResponse("usuarios_editar.html", {
        "request": request,
        "usuario": usuario,  # Pasamos el objeto usuario completo
        "usuario_actual": user_session,
        "rol_actual": rol,
        "perfil_actual": request.cookies.get("session_perfil", "usuario"),
        "rol_etiqueta_actual": "Administrador",
        "puede_exportar_actual": True,
        "puede_subir_sap_actual": True,
    })


@router.post("/usuarios/editar")
async def procesar_edicion_usuario(request: Request):
    if not request.cookies.get("session_user"):
        return RedirectResponse(url="/login", status_code=303)
    if request.cookies.get("session_rol") != "admin":
        return RedirectResponse(url="/", status_code=303)

    form = await request.form()
    try:
        id = int(str(form.get("id") or "").strip())
    except ValueError:
        return RedirectResponse(url="/usuarios", status_code=303)

    nombre = str(form.get("nombre") or "").strip()
    apellido = str(form.get("apellido") or "").strip()
    email = str(form.get("email") or "").strip()
    rol = str(form.get("rol") or "").strip()
    perfil = str(form.get("perfil") or "usuario").strip()
    activo = str(form.get("activo")) if form.get("activo") is not None else None
    if not nombre or not apellido or not email or not rol:
        return RedirectResponse(url=f"/usuarios/editar/{id}", status_code=303)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        rol_value, perfil_value = _normalize_rol_perfil(rol, perfil)
        activo_value = _as_bool_int(activo, default=0)
        sql = """
              UPDATE usuarios
              SET nombre=%s,
                  apellido=%s,
                  email=%s,
                  rol=%s,
                  perfil=%s,
                  activo=%s
              WHERE id = %s
              """
        cursor.execute(sql, (nombre, apellido, email, rol_value, perfil_value, activo_value, id))

        conn.commit()
    except Exception as e:
        print(f"Error al actualizar: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    # Una vez terminamos, volvemos a la lista de usuarios
    return RedirectResponse(url="/usuarios", status_code=303)
