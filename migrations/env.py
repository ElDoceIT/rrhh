from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection

from app.database.connection import Base, DATABASE_URL, engine

# Es necesario importar todos los modelos para registrarlos
# dentro de Base.metadata.
from app.database.models.feriado import Feriado
from app.database.models.hora_extra import HoraExtra
from app.database.models.regla_hora import ReglaHora
from app.database.models.tipo_contratacion import TipoContratacion
from app.database.models.usuario import Usuario
from app.database.models.usuario_rol import UsuarioRol


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Genera SQL sin abrir una conexión con la base."""

    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def configure_context(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta las migraciones usando la conexión del proyecto."""

    with engine.connect() as connection:
        configure_context(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
