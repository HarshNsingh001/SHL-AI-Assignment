from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.exceptions import logging_middleware, register_exception_handlers
from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    application = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
    )
    application.middleware("http")(logging_middleware)
    register_exception_handlers(application)
    application.include_router(router, prefix=resolved_settings.api_prefix)
    
    @application.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    return application
