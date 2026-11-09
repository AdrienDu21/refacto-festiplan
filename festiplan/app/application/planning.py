from app.application.errors import EntityNotFound
from app.application.event_dispatch import dispatch_events
from app.application.ports import (
    ArtistRepository,
    ConcertRepository,
    FestivalRepository,
    NotificationPort,
    StageRepository,
)
from app.domain.entities import Festival
from app.domain.policies import SchedulingPolicy


class PublishPlanning:
    def __init__(
        self,
        festivals: FestivalRepository,
        concerts: ConcertRepository,
        stages: StageRepository,
        artists: ArtistRepository,
        policy: SchedulingPolicy,
        notifier: NotificationPort,
    ):
        self._festivals = festivals
        self._concerts = concerts
        self._stages = stages
        self._artists = artists
        self._policy = policy
        self._notifier = notifier

    def execute(self, festival_id: int) -> Festival:
        festival = self._festivals.get(festival_id)
        if festival is None:
            raise EntityNotFound("Festival", festival_id)
        festival.ensure_editable()
        concerts = self._concerts.list_for_festival(festival.id)
        stages = {sid: self._stages.get(sid) for sid in {c.stage_id for c in concerts}}
        artists = {aid: self._artists.get(aid) for aid in {c.artist_id for c in concerts}}
        self._policy.validate_planning(festival, stages, artists, concerts)
        festival.publish()
        self._festivals.save(festival)
        dispatch_events(festival.pull_events(), self._notifier)
        return festival


class UnpublishPlanning:
    def __init__(self, festivals: FestivalRepository):
        self._festivals = festivals

    def execute(self, festival_id: int) -> Festival:
        festival = self._festivals.get(festival_id)
        if festival is None:
            raise EntityNotFound("Festival", festival_id)
        festival.unpublish()
        self._festivals.save(festival)
        return festival
