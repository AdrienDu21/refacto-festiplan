from dataclasses import dataclass
from datetime import datetime

from app.application.errors import ReferenceNotFound
from app.application.ports import ArtistRepository, ConcertRepository, FestivalRepository, StageRepository
from app.domain.entities import Concert
from app.domain.policies import SchedulingPolicy
from app.domain.value_objects import TimeSlot


@dataclass(frozen=True)
class ScheduleConcertCommand:
    festival_id: int
    artist_id: int
    stage_id: int
    start_time: datetime
    end_time: datetime


class ScheduleConcert:
    def __init__(
        self,
        concerts: ConcertRepository,
        festivals: FestivalRepository,
        stages: StageRepository,
        artists: ArtistRepository,
        policy: SchedulingPolicy,
    ):
        self._concerts = concerts
        self._festivals = festivals
        self._stages = stages
        self._artists = artists
        self._policy = policy

    def execute(self, command: ScheduleConcertCommand) -> Concert:
        slot = TimeSlot(command.start_time, command.end_time)
        festival = self._festivals.get(command.festival_id)
        if festival is None:
            raise ReferenceNotFound("Festival", command.festival_id)
        artist = self._artists.get(command.artist_id)
        if artist is None:
            raise ReferenceNotFound("Artiste", command.artist_id)
        stage = self._stages.get(command.stage_id)
        if stage is None:
            raise ReferenceNotFound("Scène", command.stage_id)
        self._policy.check(festival, stage, artist, slot, self._concerts.list_for_festival(festival.id))
        return self._concerts.add(Concert(None, festival.id, artist.id, stage.id, slot))
