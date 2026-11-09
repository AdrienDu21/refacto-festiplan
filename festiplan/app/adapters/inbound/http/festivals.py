from fastapi import APIRouter, Depends

from app.adapters.inbound.http.presenters import festival_out
from app.adapters.inbound.http.schemas import FestivalCreate, FestivalRead
from app.application.catalog import CreateFestival, CreateFestivalCommand
from app.application.planning import PublishPlanning, UnpublishPlanning
from app.application.queries import ListFestivals
from app.composition import (
    get_create_festival,
    get_list_festivals,
    get_publish_planning,
    get_unpublish_planning,
)

router = APIRouter(prefix="/festivals", tags=["festivals"])


@router.get("", response_model=list[FestivalRead])
def list_festivals(use_case: ListFestivals = Depends(get_list_festivals)):
    return [festival_out(f) for f in use_case.execute()]


@router.post("", response_model=FestivalRead, status_code=201)
def create_festival(payload: FestivalCreate, use_case: CreateFestival = Depends(get_create_festival)):
    command = CreateFestivalCommand(payload.name, payload.location, payload.start_date, payload.end_date)
    return festival_out(use_case.execute(command))


@router.post("/{festival_id}/publish", response_model=FestivalRead)
def publish_festival(festival_id: int, use_case: PublishPlanning = Depends(get_publish_planning)):
    return festival_out(use_case.execute(festival_id))


@router.post("/{festival_id}/unpublish", response_model=FestivalRead)
def unpublish_festival(festival_id: int, use_case: UnpublishPlanning = Depends(get_unpublish_planning)):
    return festival_out(use_case.execute(festival_id))
