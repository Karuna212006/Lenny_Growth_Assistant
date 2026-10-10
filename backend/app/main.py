from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.settings import settings
from backend.app.core.logging import setup_logging
from backend.app.core.middleware import RequestIDMiddleware
from backend.app.core.exceptions import AppError, app_error_handler, unhandled_error_handler
from backend.app.routers import health, sessions, config, artifacts, admin

setup_logging(settings.LOG_LEVEL)

app = FastAPI(title="Lenny Growth Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(config.router)
app.include_router(artifacts.router)
app.include_router(admin.router)
