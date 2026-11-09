from typing import List

from app.application.errors import EntityNotFound
from app.application.ports import ArtistRepository, ConcertRepository, FestivalRepository, StageRepository
from app.domain.entities import Artist, Concert, ConcertStatus, Festival, Stage


class ListFestivals:
    def __init__(self, festivals: FestivalRepository):
        self._festivals = festivals

    def execute(self) -> List[Festival]:
        return self._festivals.list()


class ListArtists:
    def __init__(self, artists: ArtistRepository):
        self._artists = artists

    def execute(self) -> List[Artist]:
        return self._artists.list()


class ListStages:
    def __init__(self, stages: StageRepository):
        self._stages = stages

    def execute(self, festival_id: int) -> List[Stage]:
        return self._stages.list_for_festival(festival_id)


class GetConcert:
    def __init__(self, concerts: ConcertRepository):
        self._concerts = concerts

    def execute(self, concert_id: int) -> Concert:
        concert = self._concerts.get(concert_id)
        if concert is None:
            raise EntityNotFound("Concert", concert_id)
        return concert


class ListSchedule:
    def __init__(self, concerts: ConcertRepository):
        self._concerts = concerts

    def execute(self, festival_id: int) -> List[Concert]:
        active = [c for c in self._concerts.list_for_festival(festival_id) if c.status is not ConcertStatus.CANCELLED]
        return sorted(active, key=lambda c: c.slot.start)
