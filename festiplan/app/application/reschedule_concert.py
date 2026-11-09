from dataclasses import dataclass
from datetime import datetime

from app.application.errors import EntityNotFound
from app.application.event_dispatch import dispatch_events
from app.application.ports import (
    ArtistRepository,
    ConcertRepository,
    FestivalRepository,
    NotificationPort,
    StageRepository,
)
from app.domain.entities import Concert
from app.domain.policies import SchedulingPolicy
from app.domain.value_objects import TimeSlot


@dataclass(frozen=True)
class RescheduleConcertCommand:
    concert_id: int
    start_time: datetime
    end_time: datetime


class RescheduleConcert:
    def __init__(
        self,
        concerts: ConcertRepository,
        festivals: FestivalRepository,
        stages: StageRepository,
        artists: ArtistRepository,
        policy: SchedulingPolicy,
        notifier: NotificationPort,
    ):
        self._concerts = concerts
        self._festivals = festivals
        self._stages = stages
        self._artists = artists
        self._policy = policy
        self._notifier = notifier

    def execute(self, command: RescheduleConcertCommand) -> Concert:
        concert = self._concerts.get(command.concert_id)
        if concert is None:
            raise EntityNotFound("Concert", command.concert_id)
        festival = self._festivals.get(concert.festival_id)
        stage = self._stages.get(concert.stage_id)
        artist = self._artists.get(concert.artist_id)
        new_slot = TimeSlot(command.start_time, command.end_time)
        self._policy.check(
            festival,
            stage,
            artist,
            new_slot,
            self._concerts.list_for_festival(festival.id),
            exclude_concert_id=concert.id,
        )
        concert.reschedule(new_slot)
        self._concerts.save(concert)
        dispatch_events(concert.pull_events(), self._notifier)
        return concert
