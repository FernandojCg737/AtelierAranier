from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.bitacora import router as bitacora_router
from app.api.v1.endpoints.clientes import router as clientes_router
from app.api.v1.endpoints.empleados import router as empleados_router
from app.api.v1.endpoints.perfil import router as perfil_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.sesiones import router as sesiones_router
from app.api.v1.endpoints.sucursales import router as sucursales_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(bitacora_router, prefix="/bitacora", tags=["bitacora"])
api_router.include_router(sesiones_router, prefix="/sesiones", tags=["sesiones"])
api_router.include_router(sucursales_router, prefix="/sucursales", tags=["sucursales"])
api_router.include_router(perfil_router, prefix="/perfil", tags=["perfil"])
api_router.include_router(clientes_router, prefix="/clientes", tags=["clientes"])
api_router.include_router(empleados_router, prefix="/empleados", tags=["empleados"])
api_router.include_router(roles_router, prefix="/roles", tags=["roles"])


@api_router.get("/ping", tags=["health"])
def ping() -> dict[str, str]:
    return {"status": "ok"}
