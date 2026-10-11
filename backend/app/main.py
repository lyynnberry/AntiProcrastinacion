from fastapi import FastAPI

from app.core.errors import registrar_manejadores
from app.db import registro_modelos  # noqa: F401  (SQLAlchemy necesita conocer todas las tablas)
from app.modules.auth.router import router as auth_router
from app.modules.materias.router import router as materias_router
from app.modules.tareas.router import router as tareas_router
from app.modules.usuarios.router import router as usuarios_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AntiProcrastinación API",
    version="0.1.0",
    description="Backend de RF-01 a RF-11: autenticación, tareas y materias.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
registrar_manejadores(app)
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(materias_router)
app.include_router(tareas_router)


@app.get("/salud", tags=["Sistema"])
def salud():
    return {"estado": "ok"}
