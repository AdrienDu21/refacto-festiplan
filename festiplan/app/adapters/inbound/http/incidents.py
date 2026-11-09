from fastapi import APIRouter, Depends

from app.adapters.inbound.http.presenters import incident_out
from app.adapters.inbound.http.schemas import IncidentCreate, IncidentRead
from app.application.incidents import ListIncidents, ReportIncident, ReportIncidentCommand
from app.composition import get_list_incidents, get_report_incident

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentRead, status_code=201)
def create_incident(payload: IncidentCreate, use_case: ReportIncident = Depends(get_report_incident)):
    command = ReportIncidentCommand(payload.concert_id, payload.description, payload.occurred_at)
    return incident_out(use_case.execute(command))


@router.get("", response_model=list[IncidentRead])
def list_incidents(concert_id: int | None = None, use_case: ListIncidents = Depends(get_list_incidents)):
    return [incident_out(i) for i in use_case.execute(concert_id)]
