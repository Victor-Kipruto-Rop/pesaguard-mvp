from .health import router as health_router
from .proxy import router as proxy_router
from .admin import router as admin_router

__all__ = ["health_router", "proxy_router", "admin_router"]
