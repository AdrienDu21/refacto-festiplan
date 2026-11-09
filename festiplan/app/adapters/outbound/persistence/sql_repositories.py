from typing import List, Optional

from sqlalchemy.orm import Session

from app.adapters.outbound.persistence import models as orm
from app.domain.entities import (
    Artist,
    Concert,
    ConcertStatus,
    Festival,
    Incident,
    PlanningStatus,
    Stage,
)
from app.domain.value_objects import Capacity, EquipmentSet, FestivalPeriod, TimeSlot


def _equipment_from_csv(value: str) -> EquipmentSet:
    return EquipmentSet.of(value.split(","))


def _equipment_to_csv(equipment: EquipmentSet) -> str:
    return ",".join(sorted(equipment.items))


def _concert_to_domain(row: orm.Concert) -> Concert:
    return Concert(
        id=row.id,
        festival_id=row.festival_id,
        artist_id=row.artist_id,
        stage_id=row.stage_id,
        slot=TimeSlot(row.start_time, row.end_time),
        status=ConcertStatus(row.status),
    )


def _festival_to_domain(row: orm.Festival) -> Festival:
    return Festival(
        id=row.id,
        name=row.name,
        location=row.location,
        period=FestivalPeriod(row.start_date, row.end_date),
        status=PlanningStatus(row.status),
    )


def _stage_to_domain(row: orm.Stage) -> Stage:
    return Stage(
        id=row.id,
        festival_id=row.festival_id,
        name=row.name,
        capacity=Capacity(row.capacity),
        equipment=_equipment_from_csv(row.available_equipment),
    )


def _incident_to_domain(row: orm.Incident) -> Incident:
    return Incident(
        id=row.id,
        concert_id=row.concert_id,
        description=row.description,
        occurred_at=row.occurred_at,
        resolved=row.resolved,
    )


def _artist_to_domain(row: orm.Artist) -> Artist:
    return Artist(
        id=row.id,
        name=row.name,
        genre=row.genre,
        required_equipment=_equipment_from_csv(row.required_equipment),
    )


class SqlConcertRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, concert_id: int) -> Optional[Concert]:
        row = self._db.get(orm.Concert, concert_id)
        return _concert_to_domain(row) if row else None

    def list_for_festival(self, festival_id: int) -> List[Concert]:
        rows = (
            self._db.query(orm.Concert)
            .filter(orm.Concert.festival_id == festival_id)
            .order_by(orm.Concert.start_time)
            .all()
        )
        return [_concert_to_domain(r) for r in rows]

    def add(self, concert: Concert) -> Concert:
        row = orm.Concert(
            festival_id=concert.festival_id,
            artist_id=concert.artist_id,
            stage_id=concert.stage_id,
            start_time=concert.slot.start,
            end_time=concert.slot.end,
            status=concert.status.value,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _concert_to_domain(row)

    def save(self, concert: Concert) -> None:
        row = self._db.get(orm.Concert, concert.id)
        row.stage_id = concert.stage_id
        row.start_time = concert.slot.start
        row.end_time = concert.slot.end
        row.status = concert.status.value
        self._db.commit()


class SqlFestivalRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, festival_id: int) -> Optional[Festival]:
        row = self._db.get(orm.Festival, festival_id)
        return _festival_to_domain(row) if row else None

    def list(self) -> List[Festival]:
        rows = self._db.query(orm.Festival).order_by(orm.Festival.id).all()
        return [_festival_to_domain(r) for r in rows]

    def add(self, festival: Festival) -> Festival:
        row = orm.Festival(
            name=festival.name,
            location=festival.location,
            start_date=festival.period.start,
            end_date=festival.period.end,
            status=festival.status.value,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _festival_to_domain(row)

    def save(self, festival: Festival) -> None:
        row = self._db.get(orm.Festival, festival.id)
        row.name = festival.name
        row.location = festival.location
        row.start_date = festival.period.start
        row.end_date = festival.period.end
        row.status = festival.status.value
        self._db.commit()


class SqlStageRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, stage_id: int) -> Optional[Stage]:
        row = self._db.get(orm.Stage, stage_id)
        return _stage_to_domain(row) if row else None

    def list_for_festival(self, festival_id: int) -> List[Stage]:
        rows = (
            self._db.query(orm.Stage)
            .filter(orm.Stage.festival_id == festival_id)
            .order_by(orm.Stage.id)
            .all()
        )
        return [_stage_to_domain(r) for r in rows]

    def add(self, stage: Stage) -> Stage:
        row = orm.Stage(
            festival_id=stage.festival_id,
            name=stage.name,
            capacity=stage.capacity.value,
            available_equipment=_equipment_to_csv(stage.equipment),
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _stage_to_domain(row)


class SqlArtistRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, artist_id: int) -> Optional[Artist]:
        row = self._db.get(orm.Artist, artist_id)
        return _artist_to_domain(row) if row else None

    def list(self) -> List[Artist]:
        rows = self._db.query(orm.Artist).order_by(orm.Artist.name).all()
        return [_artist_to_domain(r) for r in rows]

    def add(self, artist: Artist) -> Artist:
        row = orm.Artist(
            name=artist.name,
            genre=artist.genre,
            required_equipment=_equipment_to_csv(artist.required_equipment),
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _artist_to_domain(row)


class SqlIncidentRepository:
    def __init__(self, db: Session):
        self._db = db

    def add(self, incident: Incident) -> Incident:
        row = orm.Incident(
            concert_id=incident.concert_id,
            description=incident.description,
            occurred_at=incident.occurred_at,
            resolved=incident.resolved,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _incident_to_domain(row)

    def list(self, concert_id: Optional[int] = None) -> List[Incident]:
        query = self._db.query(orm.Incident)
        if concert_id is not None:
            query = query.filter(orm.Incident.concert_id == concert_id)
        return [_incident_to_domain(r) for r in query.order_by(orm.Incident.occurred_at.desc()).all()]
