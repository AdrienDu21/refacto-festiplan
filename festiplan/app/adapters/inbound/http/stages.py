from fastapi import APIRouter, Depends

from app.adapters.inbound.http.presenters import stage_out
from app.adapters.inbound.http.schemas import StageCreate, StageRead
from app.application.catalog import CreateStage, CreateStageCommand
from app.application.queries import ListStages
from app.composition import get_create_stage, get_list_stages

router = APIRouter(prefix="/stages", tags=["stages"])


@router.get("", response_model=list[StageRead])
def list_stages(festival_id: int, use_case: ListStages = Depends(get_list_stages)):
    return [stage_out(s) for s in use_case.execute(festival_id)]


@router.post("", response_model=StageRead, status_code=201)
def create_stage(payload: StageCreate, use_case: CreateStage = Depends(get_create_stage)):
    command = CreateStageCommand(payload.festival_id, payload.name, payload.capacity, payload.available_equipment)
    return stage_out(use_case.execute(command))
