"""
Global exception handlers to ensure 100% consistent JSON error responses across the API.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.schemas.common import ErrorDetail, ResponseMeta, StandardErrorResponse

logger = logging.getLogger("gridguard.handlers")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(f"AppException [{exc.code}] on {request.method} {request.url.path}: {exc.message}")
        content = StandardErrorResponse(
            status="error",
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
            meta=ResponseMeta(request_id=request.headers.get("x-request-id")),
        ).model_dump(mode="json")
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.info(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
        first_error = exc.errors()[0] if exc.errors() else {}
        loc = " -> ".join([str(x) for x in first_error.get("loc", []) if x != "body"])
        msg = first_error.get("msg", "Invalid request parameter")
        
        content = StandardErrorResponse(
            status="error",
            error=ErrorDetail(
                code="ERR_VALIDATION_FAILED",
                message=f"Validation failed: {msg}" + (f" for field '{loc}'" if loc else ""),
                field=loc or None,
                details=[
                    {
                        "field": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
                        "message": err.get("msg"),
                        "type": err.get("type"),
                    }
                    for err in exc.errors()
                ],
            ),
            meta=ResponseMeta(request_id=request.headers.get("x-request-id")),
        ).model_dump(mode="json")
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            404: "ERR_RESOURCE_NOT_FOUND",
            405: "ERR_METHOD_NOT_ALLOWED",
            403: "ERR_FORBIDDEN",
            401: "ERR_UNAUTHORIZED",
            500: "ERR_INTERNAL_SERVER_ERROR",
            503: "ERR_SERVICE_UNAVAILABLE",
        }
        err_code = code_map.get(exc.status_code, f"ERR_HTTP_{exc.status_code}")
        content = StandardErrorResponse(
            status="error",
            error=ErrorDetail(
                code=err_code,
                message=str(exc.detail) if exc.detail else "HTTP error encountered",
            ),
            meta=ResponseMeta(request_id=request.headers.get("x-request-id")),
        ).model_dump(mode="json")
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled system exception on {request.method} {request.url.path}: {str(exc)}")
        content = StandardErrorResponse(
            status="error",
            error=ErrorDetail(
                code="ERR_INTERNAL_SERVER_ERROR",
                message="An unexpected system error occurred while processing the request",
                details=str(exc) if app.debug else None,
            ),
            meta=ResponseMeta(request_id=request.headers.get("x-request-id")),
        ).model_dump(mode="json")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)
