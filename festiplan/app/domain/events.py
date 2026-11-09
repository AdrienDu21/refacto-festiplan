from dataclasses import dataclass

from app.domain.value_objects import TimeSlot


@dataclass(frozen=True)
class ConcertRescheduled:
    concert_id: int
    festival_id: int
    old_slot: TimeSlot
    new_slot: TimeSlot


@dataclass(frozen=True)
class ConcertCancelled:
    concert_id: int
    festival_id: int


@dataclass(frozen=True)
class PlanningPublished:
    festival_id: int
