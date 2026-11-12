from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

class PolyGenException(Exception):
    """Base exception for all PolyGen domain errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

class EntityNotFoundException(PolyGenException):
    def __init__(self, entity_name: str, entity_id: str):
        super().__init__(
            message=f"{entity_name} with id '{entity_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )

class AuthenticationException(PolyGenException):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )

class AuthorizationException(PolyGenException):
    def __init__(self, message: str = "You do not have permission to access this resource"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )

class ValidationException(PolyGenException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR"
        )

class PipelineExecutionException(PolyGenException):
    def __init__(self, stage: str, message: str):
        super().__init__(
            message=f"Pipeline error at stage '{stage}': {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="PIPELINE_ERROR"
        )

def register_error_handlers(app: FastAPI):
    """Registers global exception handlers for consistent API error contracts."""

    @app.exception_handler(PolyGenException)
    async def handle_polygen_exception(request: Request, exc: PolyGenException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "path": request.url.path,
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            errors.append({"field": loc, "message": err.get("msg")})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "details": errors,
                    "path": request.url.path,
                }
            }
        )

