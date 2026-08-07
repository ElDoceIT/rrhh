from datetime import timedelta

from database import get_connection
from services.recalculo import run_recalculo_estados
from services.timezone import now_argentina

META_KEY_RECALCULO_LOGIN = "ultimo_disparo_recalculo_por_login"
RECALCULO_COOLDOWN_HORAS = 5


def _ensure_meta_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            clave VARCHAR(100) PRIMARY KEY,
            valor_datetime DATETIME NULL,
            actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)


def _get_ultimo_disparo(cursor):
    cursor.execute("""
        SELECT valor_datetime
        FROM app_meta
        WHERE clave = %s
        LIMIT 1
    """, (META_KEY_RECALCULO_LOGIN,))
    row = cursor.fetchone()
    if not row:
        return None
    return row[0]


def _set_ultimo_disparo(cursor, ts):
    cursor.execute("""
        INSERT INTO app_meta (clave, valor_datetime)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE valor_datetime = VALUES(valor_datetime)
    """, (META_KEY_RECALCULO_LOGIN, ts))


def on_user_login(_username: str) -> dict:
    """
    Hook listo para usar cuando exista login.
    Regla: ejecuta recálculo solo si pasaron más de 5 horas desde el último disparo.
    """
    conn = get_connection()
    if conn is None:
        return {"ok": False, "executed": False, "reason": "db_unavailable"}

    cursor = conn.cursor()
    _ensure_meta_table(cursor)

    ahora = now_argentina()
    ultimo = _get_ultimo_disparo(cursor)
    cooldown = timedelta(hours=RECALCULO_COOLDOWN_HORAS)

    if ultimo is not None and (ahora - ultimo) < cooldown:
        cursor.close()
        conn.close()
        return {"ok": True, "executed": False, "reason": "cooldown"}

    actualizadas = run_recalculo_estados(conn)
    _set_ultimo_disparo(cursor, ahora)
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "ok": True,
        "executed": True,
        "reason": "run",
        "actualizadas": actualizadas,
        "executed_at": ahora.isoformat(sep=" "),
    }
