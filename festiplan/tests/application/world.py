from datetime import datetime

from app.domain.entities import Artist, Concert, Festival, Stage
from app.domain.policies import SchedulingPolicy
from app.domain.value_objects import Capacity, EquipmentSet, FestivalPeriod, TimeSlot
from fakes import (
    InMemoryArtistRepository,
    InMemoryConcertRepository,
    InMemoryFestivalRepository,
    InMemoryIncidentRepository,
    InMemoryStageRepository,
    RecordingNotifier,
)


def at(hour, minute=0, day=18):
    return datetime(2027, 6, day, hour, minute)


def slot(h1, h2):
    return TimeSlot(at(h1), at(h2))


class World:
    def __init__(self, notifier=None):
        self.concerts = InMemoryConcertRepository()
        self.festivals = InMemoryFestivalRepository()
        self.stages = InMemoryStageRepository()
        self.artists = InMemoryArtistRepository()
        self.incidents = InMemoryIncidentRepository()
        self.policy = SchedulingPolicy()
        self.notifier = notifier or RecordingNotifier()
        self.festival = self.festivals.add(
            Festival(None, "Hellforge", "Clisson", FestivalPeriod(at(10), at(23, day=20)))
        )
        self.main = self.stages.add(Stage(None, self.festival.id, "Main", Capacity(1000), EquipmentSet.of(["lights"])))
        self.side = self.stages.add(Stage(None, self.festival.id, "Side", Capacity(500), EquipmentSet.of([])))
        self.artist_a = self.artists.add(Artist(None, "A", "Metal", EquipmentSet.of([])))
        self.artist_b = self.artists.add(Artist(None, "B", "Metal", EquipmentSet.of([])))
        self.c1 = self.add_concert(self.artist_a, self.main, slot(18, 19))
        self.c2 = self.add_concert(self.artist_b, self.main, slot(19, 20))
        self.c3 = self.add_concert(self.artist_b, self.side, slot(21, 22))

    def add_concert(self, artist, stage, s):
        return self.concerts.add(Concert(None, self.festival.id, artist.id, stage.id, s))
