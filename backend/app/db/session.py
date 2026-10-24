from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# La sesión de PostgreSQL trabaja siempre en UTC: así las fechas con zona horaria se devuelven de forma
# consistente sin importar la configuración del servidor.
engine = create_engine(
    settings.database_url, pool_pre_ping=True, connect_args={"options": "-c timezone=UTC"}
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
