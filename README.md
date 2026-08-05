# Horas extras

## Configuración

Copiar `.env.example` como `.env` y completar la conexión a la base y Active
Directory. Aplicar las migraciones antes de iniciar la aplicación:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

## Administrador local de emergencia

Al arrancar, la aplicación intenta crear un usuario local idempotente. Solo lo
crea cuando `SEED_ADMIN_PASSWORD` tiene un valor y el nombre configurado en
`SEED_ADMIN_USERNAME` también está incluido en `AUTH_LOCAL_USERS` (comparación
sin distinguir mayúsculas y minúsculas). La contraseña se almacena únicamente
como hash bcrypt y nunca se escribe en el log.

Variables disponibles:

- `SEED_ADMIN_USERNAME` (predeterminado: `admin`)
- `SEED_ADMIN_PASSWORD` (obligatoria para crear el seed, sin valor predeterminado)
- `SEED_ADMIN_NOMBRE` (predeterminado: `Admin`)
- `SEED_ADMIN_APELLIDO` (predeterminado: `Local`)
- `SEED_ADMIN_EMAIL` (predeterminado: `admin@local.invalid`)
- `AUTH_LOCAL_USERS` (predeterminado: `admin,root`)

Si el usuario ya existe, el arranque no modifica su contraseña, estado, rol ni
ningún otro dato. Los nombres de `AUTH_LOCAL_USERS` se autentican exclusivamente
contra su hash local y nunca se envían a AD. Los demás usuarios conservan la
validación por AD y, después, deben existir activos en la base local, de donde se
cargan su rol y permisos.

Este repositorio actualmente no contiene una tarea de sincronización de AD. Una
sincronización futura debe usar `local_usernames()`/`is_local_username()` de
`app.services.local_auth` para excluir esas cuentas de cualquier alta, cambio,
desactivación o eliminación.
