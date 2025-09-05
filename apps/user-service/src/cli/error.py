from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from src.domains.common import exceptions as ex

def install_exception_handlers(app: FastAPI) -> None:
    EXC_MAP = {
        ex.DuplicateEmail:      status.HTTP_409_CONFLICT,
        ex.DuplicateUsername:   status.HTTP_409_CONFLICT,
        ex.Conflict:            status.HTTP_409_CONFLICT,
        ex.DatabaseConflict:    status.HTTP_409_CONFLICT,
        ex.NotFound:            status.HTTP_404_NOT_FOUND,
        ex.ValidationFailed:    status.HTTP_422_UNPROCESSABLE_ENTITY,
        ex.Unauthorized:        status.HTTP_401_UNAUTHORIZED,
        ex.Forbidden:           status.HTTP_403_FORBIDDEN,
        ex.DomainError:         status.HTTP_400_BAD_REQUEST,
    }

    for exc_type, http_code in EXC_MAP.items():
        @app.exception_handler(exc_type)
        async def _handler(request: Request, exc: exc_type, __code=http_code):
            cid = getattr(request.state, "correlation_id", None)
            return JSONResponse(
                status_code=__code,
                content={
                    "error": {
                        "type": exc.__class__.__name__,
                        "code": getattr(exc, "code", "error"),
                        "message": str(exc) or exc.__class__.__name__,
                        "correlation_id": cid,
                    }
                },
            )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        cid = getattr(request.state, "correlation_id", None)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {
                "type": "InternalServerError",
                "code": "internal_error",
                "message": "Internal server error",
                "correlation_id": cid,
            }},
        )
