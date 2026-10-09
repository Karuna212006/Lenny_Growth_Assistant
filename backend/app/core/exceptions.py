from fastapi import Request
from fastapi.responses import JSONResponse
import structlog.contextvars

class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 500):
        self.code = code
        self.message = message
        self.status = status

async def app_error_handler(request: Request, exc: AppError):
    ctx = structlog.contextvars.get_contextvars()
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message,
                           "request_id": ctx.get("request_id", "")}},
    )

async def unhandled_error_handler(request: Request, exc: Exception):
    ctx = structlog.contextvars.get_contextvars()
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred.",
                           "request_id": ctx.get("request_id", "")}},
    )
