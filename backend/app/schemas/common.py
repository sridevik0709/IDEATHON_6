"""
Standard response and error envelope schemas.
Enforces a consistent API structure across all endpoints.
"""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ResponseMeta(BaseModel):
    version: str = Field(default="1.0.0-level1", description="API Version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of response generation"
    )
    request_id: Optional[str] = Field(default=None, description="Unique correlation ID for tracing")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    field: Optional[str] = Field(default=None, description="Target field in payload if validation error")
    details: Optional[Any] = Field(default=None, description="Detailed diagnostic or traceback context")


class StandardSuccessResponse(BaseModel, Generic[DataT]):
    status: str = Field(default="success", description="Status indicator: success")
    data: DataT = Field(..., description="Payload data")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")


class StandardErrorResponse(BaseModel):
    status: str = Field(default="error", description="Status indicator: error")
    error: ErrorDetail = Field(..., description="Structured error information")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")
