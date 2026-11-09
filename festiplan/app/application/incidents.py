from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List, Optional

from app.application.errors import EntityNotFound
from app.application.ports import ConcertRepository, IncidentRepository
from app.domain.entities import Incident


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True)
class ReportIncidentCommand:
    concert_id: int
    description: str
    occurred_at: Optional[datetime] = None


class ReportIncident:
    def __init__(self, concerts: ConcertRepository, incidents: IncidentRepository, clock: Callable[[], datetime] = utc_now):
        self._concerts = concerts
        self._incidents = incidents
        self._clock = clock

    def execute(self, command: ReportIncidentCommand) -> Incident:
        if self._concerts.get(command.concert_id) is None:
            raise EntityNotFound("Concert", command.concert_id)
        incident = Incident(None, command.concert_id, command.description, command.occurred_at or self._clock())
        return self._incidents.add(incident)


class ListIncidents:
    def __init__(self, incidents: IncidentRepository):
        self._incidents = incidents

    def execute(self, concert_id: Optional[int] = None) -> List[Incident]:
        return self._incidents.list(concert_id)
