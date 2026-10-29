"""
Custom application exception hierarchy for GridGuard Nexus X.
Provides consistent error codes and structured context.
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception class for all domain and platform exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "ERR_INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ResourceNotFoundException(AppException):
    def __init__(self, message: str = "Requested resource was not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="ERR_RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class ValidationFailedException(AppException):
    def __init__(self, message: str = "Request validation failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="ERR_VALIDATION_FAILED",
            status_code=422,
            details=details,
        )


class ConfigurationException(AppException):
    def __init__(self, message: str = "Invalid or missing configuration", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="ERR_CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )


class DatabaseUnavailableException(AppException):
    def __init__(self, message: str = "Database service unavailable", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="ERR_DATABASE_UNAVAILABLE",
            status_code=503,
            details=details,
        )
