from fastapi import APIRouter, Depends

from app.adapters.inbound.http.presenters import concert_out
from app.adapters.inbound.http.schemas import ConcertCreate, ConcertRead, ConcertReschedule
from app.application.cancel_concert import CancelConcert
from app.application.queries import GetConcert, ListSchedule
from app.application.reschedule_concert import RescheduleConcert, RescheduleConcertCommand
from app.application.schedule_concert import ScheduleConcert, ScheduleConcertCommand
from app.composition import (
    get_cancel_concert,
    get_concert,
    get_list_schedule,
    get_reschedule_concert,
    get_schedule_concert,
)

router = APIRouter(prefix="/concerts", tags=["concerts"])


@router.get("", response_model=list[ConcertRead])
def list_concerts(festival_id: int, use_case: ListSchedule = Depends(get_list_schedule)):
    return [concert_out(c) for c in use_case.execute(festival_id)]


@router.get("/schedule/{festival_id}", response_model=list[ConcertRead])
def get_schedule(festival_id: int, use_case: ListSchedule = Depends(get_list_schedule)):
    return [concert_out(c) for c in use_case.execute(festival_id)]


@router.get("/{concert_id}", response_model=ConcertRead)
def read_concert(concert_id: int, use_case: GetConcert = Depends(get_concert)):
    return concert_out(use_case.execute(concert_id))


@router.post("", response_model=ConcertRead, status_code=201)
def create_concert(payload: ConcertCreate, use_case: ScheduleConcert = Depends(get_schedule_concert)):
    command = ScheduleConcertCommand(
        payload.festival_id, payload.artist_id, payload.stage_id, payload.start_time, payload.end_time
    )
    return concert_out(use_case.execute(command))


@router.patch("/{concert_id}/reschedule", response_model=ConcertRead)
def reschedule_concert(
    concert_id: int, payload: ConcertReschedule, use_case: RescheduleConcert = Depends(get_reschedule_concert)
):
    command = RescheduleConcertCommand(concert_id, payload.start_time, payload.end_time)
    return concert_out(use_case.execute(command))


@router.post("/{concert_id}/cancel", response_model=ConcertRead)
def cancel_concert(concert_id: int, use_case: CancelConcert = Depends(get_cancel_concert)):
    return concert_out(use_case.execute(concert_id))
