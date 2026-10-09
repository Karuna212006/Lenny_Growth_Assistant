from fastapi import Request
from fastapi.responses import JSONResponse
try:
    import structlog.contextvars
    def _get_request_id() -> str:
        return structlog.contextvars.get_contextvars().get("request_id", "")
except (ImportError, AttributeError):
    def _get_request_id() -> str:
        return ""

class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 500):
        self.code = code
        self.message = message
        self.status = status

async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message,
                           "request_id": _get_request_id()}},
    )

async def unhandled_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred.",
                           "request_id": _get_request_id()}},
    )

