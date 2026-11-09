from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.errors import EntityNotFound, ReferenceNotFound
from app.domain.errors import (
    ConcertAlreadyCancelled,
    DomainError,
    PlanningLocked,
    PlanningNotPublished,
)

_CONFLICTS = (PlanningLocked, PlanningNotPublished, ConcertAlreadyCancelled)


def status_for(exc: Exception) -> int:
    if isinstance(exc, ReferenceNotFound):
        return 400
    if isinstance(exc, EntityNotFound):
        return 404
    if isinstance(exc, _CONFLICTS):
        return 409
    return 400


def register_error_handlers(app: FastAPI) -> None:
    async def handle(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_for(exc), content={"detail": str(exc)})

    app.add_exception_handler(DomainError, handle)
    app.add_exception_handler(EntityNotFound, handle)
