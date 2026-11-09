from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from app.domain.errors import (
    ConcertAlreadyCancelled,
    InvalidIncident,
    PlanningLocked,
    PlanningNotPublished,
)
from app.domain.events import ConcertCancelled, ConcertRescheduled, PlanningPublished
from app.domain.value_objects import Capacity, EquipmentSet, FestivalPeriod, TimeSlot


class ConcertStatus(str, Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


class PlanningStatus(str, Enum):
    PREPARATION = "preparation"
    PUBLISHED = "published"


@dataclass
class Artist:
    id: Optional[int]
    name: str
    genre: str
    required_equipment: EquipmentSet


@dataclass
class Stage:
    id: Optional[int]
    festival_id: int
    name: str
    capacity: Capacity
    equipment: EquipmentSet


@dataclass
class Concert:
    id: Optional[int]
    festival_id: int
    artist_id: int
    stage_id: int
    slot: TimeSlot
    status: ConcertStatus = ConcertStatus.SCHEDULED
    _events: list = field(default_factory=list, repr=False, compare=False)

    def reschedule(self, new_slot: TimeSlot) -> None:
        if self.status is ConcertStatus.CANCELLED:
            raise ConcertAlreadyCancelled("Un concert annulé ne peut pas être déplacé")
        old_slot = self.slot
        self.slot = new_slot
        self._events.append(ConcertRescheduled(self.id, self.festival_id, old_slot, new_slot))

    def cancel(self) -> None:
        if self.status is ConcertStatus.CANCELLED:
            return
        self.status = ConcertStatus.CANCELLED
        self._events.append(ConcertCancelled(self.id, self.festival_id))

    def pull_events(self) -> list:
        events, self._events = self._events, []
        return events


@dataclass
class Festival:
    id: Optional[int]
    name: str
    location: str
    period: FestivalPeriod
    status: PlanningStatus = PlanningStatus.PREPARATION
    _events: list = field(default_factory=list, repr=False, compare=False)

    @property
    def is_published(self) -> bool:
        return self.status is PlanningStatus.PUBLISHED

    def ensure_editable(self) -> None:
        if self.is_published:
            raise PlanningLocked("Le planning est publié : dépubliez-le avant de le modifier")

    def publish(self) -> None:
        self.ensure_editable()
        self.status = PlanningStatus.PUBLISHED
        self._events.append(PlanningPublished(self.id))

    def unpublish(self) -> None:
        if not self.is_published:
            raise PlanningNotPublished("Le planning n'est pas publié")
        self.status = PlanningStatus.PREPARATION

    def pull_events(self) -> list:
        events, self._events = self._events, []
        return events


@dataclass
class Incident:
    id: Optional[int]
    concert_id: int
    description: str
    occurred_at: datetime
    resolved: bool = False

    def __post_init__(self):
        self.description = self.description.strip()
        if not self.description:
            raise InvalidIncident("La description d'un incident ne peut pas être vide")
