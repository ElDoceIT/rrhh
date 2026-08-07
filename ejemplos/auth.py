import os
from fastapi import APIRouter, Request, Form, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_connection
from services.login_hooks import on_user_login
from services.ad_sync import authenticate_user as authenticate_against_ad
import bcrypt
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# --- FUNCIONES DE SEGURIDAD (Hash y Verificación) ---

def hash_password(password: str):
    """Genera un hash seguro para la v0.9 usando bcrypt directamente."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str):
    """Compara texto plano con el hash de la base de datos."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def _local_users() -> set[str]:
    users = os.getenv("AUTH_LOCAL_USERS", "admin,root")
    return {u.strip().lower() for u in users.split(",") if u.strip()}


def _normalize_login_username(username: str) -> str:
    value = username.strip()
    if "\\" in value:
        value = value.split("\\", 1)[1]
    if "@" in value:
        value = value.split("@", 1)[0]
    return value.strip()


# --- DEPENDENCIAS (Para proteger otras rutas) ---

def get_current_user(request: Request):
    """Verifica si hay una sesión activa. Se usa con Depends()."""
    user = request.cookies.get("session_user")
    if not user:
        # Si no hay usuario, lanzamos excepción para redirigir al login
        raise HTTPException(status_code=303, detail="No logueado")
    return user


def admin_only(request: Request):
    """Verifica que el usuario sea administrador."""
    rol = request.cookies.get("session_rol")
    if rol != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere ser administrador")
    return rol


def normalize_perfil(perfil: str | None) -> str:
    return (perfil or "usuario").strip().lower() or "usuario"


def etiqueta_rol_usuario(user_ctx: dict | None) -> str:
    if not user_ctx:
        return ""

    rol = (user_ctx.get("rol") or "").strip().lower()
    perfil = normalize_perfil(user_ctx.get("perfil"))
    if rol == "admin":
        return "Administrador"
    if rol == "operador":
        return "Operador Jefe" if perfil == "jefe" else "Operador"
    if rol == "vendedor":
        return "Vendedor Jefe" if perfil == "jefe" else "Vendedor"
    return rol or "Sin rol"


def es_vendedor_usuario(user_ctx: dict | None) -> bool:
    if not user_ctx:
        return False
    return user_ctx.get("rol") == "vendedor" and normalize_perfil(user_ctx.get("perfil")) == "usuario"


def puede_ver_todos_los_clientes(user_ctx: dict | None) -> bool:
    return not es_vendedor_usuario(user_ctx)


def puede_subir_sap(user_ctx_or_rol) -> bool:
    rol = user_ctx_or_rol.get("rol") if isinstance(user_ctx_or_rol, dict) else user_ctx_or_rol
    return rol in {"admin", "operador"}


def puede_exportar(user_ctx: dict | None) -> bool:
    if not user_ctx:
        return False
    if user_ctx.get("rol") in {"admin", "operador"}:
        return True
    return user_ctx.get("rol") == "vendedor" and normalize_perfil(user_ctx.get("perfil")) == "jefe"


def session_template_context(user_ctx: dict | None) -> dict:
    if not user_ctx:
        return {}
    return {
        "usuario_actual": user_ctx.get("username"),
        "rol_actual": user_ctx.get("rol"),
        "perfil_actual": normalize_perfil(user_ctx.get("perfil")),
        "rol_etiqueta_actual": etiqueta_rol_usuario(user_ctx),
        "puede_exportar_actual": puede_exportar(user_ctx),
        "puede_subir_sap_actual": puede_subir_sap(user_ctx),
    }


def get_session_context(request: Request):
    username = request.cookies.get("session_user")
    rol = request.cookies.get("session_rol")

    if not username:
        return None

    conn = get_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, username, rol, perfil, activo
        FROM usuarios
        WHERE username = %s
        LIMIT 1
    """, (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return None
    if int(user.get("activo", 1) or 0) != 1:
        return None

    user["perfil"] = normalize_perfil(user.get("perfil"))
    return user


def cliente_permitido_para_usuario(cursor, user_ctx, cuenta: int) -> bool:
    if not user_ctx:
        return False

    if not es_vendedor_usuario(user_ctx):
        return True

    cursor.execute("""
        SELECT 1
        FROM clientes
        WHERE cuenta = %s AND operador = %s
        LIMIT 1
    """, (cuenta, user_ctx["id"]))
    return cursor.fetchone() is not None


# --- RUTAS DE LOGIN / LOGOUT ---

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = None):
    # Asegúrate de que en login.html el input de usuario NO tenga value="lbollini"
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    username = _normalize_login_username(username)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # El usuario debe existir en la BD local para obtener rol/permisos.
    cursor.execute(
        """
        SELECT username, password_hash, rol, perfil, activo
        FROM usuarios
        WHERE LOWER(username) = LOWER(%s)
        LIMIT 1
        """,
        (username,),
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return RedirectResponse(url="/login?error=1", status_code=303)
    if int(user.get("activo", 1) or 0) != 1:
        return RedirectResponse(url="/login?error=1", status_code=303)

    is_local_user = username.lower() in _local_users()
    login_ok = False

    if is_local_user:
        stored_hash = user.get("password_hash")
        if stored_hash:
            login_ok = verify_password(password, stored_hash)
    else:
        login_ok = authenticate_against_ad(username, password)

    if login_ok:
        # No bloquear login si falla el hook de recálculo
        try:
            on_user_login(user["username"])
        except Exception as e:
            print(f"[login_hook] no se pudo ejecutar recálculo: {e}")

        res = RedirectResponse(url="/", status_code=303)

        # Seteamos cookies con httponly para seguridad en El Doce
        res.set_cookie(key="session_user", value=user["username"], httponly=True)
        res.set_cookie(key="session_rol", value=user["rol"], httponly=True)
        res.set_cookie(key="session_perfil", value=normalize_perfil(user.get("perfil")), httponly=True)

        return res

    # Si los datos son incorrectos, vuelve al login
    return RedirectResponse(url="/login?error=1", status_code=303)


@router.get("/logout")
def logout():
    """Cierra la sesión limpiando todas las cookies de cobranzas."""
    res = RedirectResponse(url="/login", status_code=303)
    res.delete_cookie("session_user")
    res.delete_cookie("session_rol")
    res.delete_cookie("session_perfil")
    return res
