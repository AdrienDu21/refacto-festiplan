from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.domain.errors import InvalidCapacity, InvalidFestivalPeriod, InvalidTimeSlot


@dataclass(frozen=True)
class TimeSlot:
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.end <= self.start:
            raise InvalidTimeSlot("La fin du créneau doit être postérieure à son début")

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class FestivalPeriod:
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.end <= self.start:
            raise InvalidFestivalPeriod("La fin du festival doit être postérieure à son début")

    def contains(self, slot: TimeSlot) -> bool:
        return self.start <= slot.start and slot.end <= self.end


@dataclass(frozen=True)
class EquipmentSet:
    items: frozenset = frozenset()

    def __post_init__(self):
        cleaned = frozenset(i.strip() for i in self.items if i and i.strip())
        object.__setattr__(self, "items", cleaned)

    @classmethod
    def of(cls, items: Iterable[str]) -> "EquipmentSet":
        return cls(frozenset(items))

    def covers(self, required: "EquipmentSet") -> bool:
        return required.items <= self.items

    def missing(self, required: "EquipmentSet") -> frozenset:
        return required.items - self.items


@dataclass(frozen=True)
class Capacity:
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise InvalidCapacity("La capacité doit être strictement positive")
