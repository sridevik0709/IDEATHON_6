"""
Response construction utilities.
"""

from typing import Any, Optional
from app.schemas.common import ResponseMeta, StandardSuccessResponse


def success_response(data: Any, request_id: Optional[str] = None) -> StandardSuccessResponse:
    """Helper to wrap any payload data in the standard success envelope."""
    return StandardSuccessResponse(
        status="success",
        data=data,
        meta=ResponseMeta(request_id=request_id),
    )
