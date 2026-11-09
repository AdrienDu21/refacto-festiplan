from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.outbound.persistence import models
from app.adapters.outbound.persistence.sql_repositories import (
    SqlArtistRepository,
    SqlConcertRepository,
    SqlFestivalRepository,
    SqlIncidentRepository,
    SqlStageRepository,
)
from app.adapters.outbound.persistence.database import Base
from app.domain.entities import Artist, Concert, ConcertStatus, Festival, Incident, PlanningStatus, Stage
from app.domain.value_objects import Capacity, EquipmentSet, FestivalPeriod, TimeSlot


def at(hour, day=18):
    return datetime(2027, 6, day, hour)


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def world(db):
    festival = SqlFestivalRepository(db).add(
        Festival(None, "Hellforge", "Clisson", FestivalPeriod(at(10), at(23, day=20)))
    )
    stage = SqlStageRepository(db).add(
        Stage(None, festival.id, "Main", Capacity(1000), EquipmentSet.of(["lights", "rigging"]))
    )
    artist = SqlArtistRepository(db).add(Artist(None, "Iron Vow", "Metal", EquipmentSet.of(["lights"])))
    return festival, stage, artist


def test_festival_round_trip(db, world):
    festival, _, _ = world
    loaded = SqlFestivalRepository(db).get(festival.id)
    assert loaded.name == "Hellforge"
    assert loaded.period == FestivalPeriod(at(10), at(23, day=20))
    assert loaded.status is PlanningStatus.PREPARATION


def test_festival_status_is_persisted(db, world):
    festival, _, _ = world
    repo = SqlFestivalRepository(db)
    festival.publish()
    repo.save(festival)
    assert repo.get(festival.id).is_published
    assert db.get(models.Festival, festival.id).status == "published"


def test_stage_equipment_round_trip(db, world):
    _, stage, _ = world
    loaded = SqlStageRepository(db).get(stage.id)
    assert loaded.equipment == EquipmentSet.of(["lights", "rigging"])
    assert loaded.capacity == Capacity(1000)


def test_artist_equipment_round_trip(db, world):
    _, _, artist = world
    assert SqlArtistRepository(db).get(artist.id).required_equipment == EquipmentSet.of(["lights"])


def test_unknown_entities_return_none(db):
    assert SqlConcertRepository(db).get(1) is None
    assert SqlFestivalRepository(db).get(1) is None
    assert SqlStageRepository(db).get(1) is None
    assert SqlArtistRepository(db).get(1) is None


def test_concert_round_trip_and_save(db, world):
    festival, stage, artist = world
    repo = SqlConcertRepository(db)
    concert = repo.add(Concert(None, festival.id, artist.id, stage.id, TimeSlot(at(18), at(19))))
    assert concert.id is not None
    concert.reschedule(TimeSlot(at(20), at(21)))
    repo.save(concert)
    loaded = repo.get(concert.id)
    assert loaded.slot == TimeSlot(at(20), at(21))
    assert loaded.status is ConcertStatus.SCHEDULED


def test_cancelled_status_is_persisted(db, world):
    festival, stage, artist = world
    repo = SqlConcertRepository(db)
    concert = repo.add(Concert(None, festival.id, artist.id, stage.id, TimeSlot(at(18), at(19))))
    concert.cancel()
    repo.save(concert)
    assert repo.get(concert.id).status is ConcertStatus.CANCELLED


def test_concerts_are_listed_by_festival_in_chronological_order(db, world):
    festival, stage, artist = world
    repo = SqlConcertRepository(db)
    late = repo.add(Concert(None, festival.id, artist.id, stage.id, TimeSlot(at(21), at(22))))
    early = repo.add(Concert(None, festival.id, artist.id, stage.id, TimeSlot(at(18), at(19))))
    assert [c.id for c in repo.list_for_festival(festival.id)] == [early.id, late.id]
    assert repo.list_for_festival(999) == []


def test_incident_round_trip_and_ordering(db, world):
    festival, stage, artist = world
    concert = SqlConcertRepository(db).add(Concert(None, festival.id, artist.id, stage.id, TimeSlot(at(18), at(19))))
    repo = SqlIncidentRepository(db)
    first = repo.add(Incident(None, concert.id, "Premier", at(18)))
    second = repo.add(Incident(None, concert.id, "Second", at(19)))
    assert first.id is not None and first.resolved is False
    assert [i.description for i in repo.list(concert.id)] == ["Second", "Premier"]
    assert len(repo.list()) == 2
    assert repo.list(999) == []
