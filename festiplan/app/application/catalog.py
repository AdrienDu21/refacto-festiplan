from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from app.application.errors import ReferenceNotFound
from app.application.ports import ArtistRepository, FestivalRepository, StageRepository
from app.domain.entities import Artist, Festival, Stage
from app.domain.value_objects import Capacity, EquipmentSet, FestivalPeriod


@dataclass(frozen=True)
class CreateFestivalCommand:
    name: str
    location: str
    start_date: datetime
    end_date: datetime


@dataclass(frozen=True)
class CreateStageCommand:
    festival_id: int
    name: str
    capacity: int
    available_equipment: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CreateArtistCommand:
    name: str
    genre: str
    required_equipment: List[str] = field(default_factory=list)


class CreateFestival:
    def __init__(self, festivals: FestivalRepository):
        self._festivals = festivals

    def execute(self, command: CreateFestivalCommand) -> Festival:
        period = FestivalPeriod(command.start_date, command.end_date)
        return self._festivals.add(Festival(None, command.name, command.location, period))


class CreateStage:
    def __init__(self, festivals: FestivalRepository, stages: StageRepository):
        self._festivals = festivals
        self._stages = stages

    def execute(self, command: CreateStageCommand) -> Stage:
        capacity = Capacity(command.capacity)
        if self._festivals.get(command.festival_id) is None:
            raise ReferenceNotFound("Festival", command.festival_id)
        equipment = EquipmentSet.of(command.available_equipment)
        return self._stages.add(Stage(None, command.festival_id, command.name, capacity, equipment))


class CreateArtist:
    def __init__(self, artists: ArtistRepository):
        self._artists = artists

    def execute(self, command: CreateArtistCommand) -> Artist:
        equipment = EquipmentSet.of(command.required_equipment)
        return self._artists.add(Artist(None, command.name, command.genre, equipment))
