from typing import Iterable, Mapping, Optional

from app.domain.entities import Artist, Concert, ConcertStatus, Festival, Stage
from app.domain.errors import (
    ArtistSlotConflict,
    MissingEquipment,
    OutsideFestivalPeriod,
    StageNotInFestival,
    StageSlotConflict,
)
from app.domain.value_objects import TimeSlot


class SchedulingPolicy:
    def check(
        self,
        festival: Festival,
        stage: Stage,
        artist: Artist,
        slot: TimeSlot,
        festival_concerts: Iterable[Concert],
        exclude_concert_id: Optional[int] = None,
    ) -> None:
        festival.ensure_editable()
        self._check_rules(festival, stage, artist, slot, festival_concerts, exclude_concert_id)

    def validate_planning(
        self,
        festival: Festival,
        stages: Mapping[int, Stage],
        artists: Mapping[int, Artist],
        festival_concerts: Iterable[Concert],
    ) -> None:
        concerts = list(festival_concerts)
        for concert in concerts:
            if concert.status is ConcertStatus.CANCELLED:
                continue
            self._check_rules(
                festival,
                stages[concert.stage_id],
                artists[concert.artist_id],
                concert.slot,
                concerts,
                concert.id,
            )

    def _check_rules(self, festival, stage, artist, slot, festival_concerts, exclude_concert_id):
        if stage.festival_id != festival.id:
            raise StageNotInFestival("La scène n'appartient pas à ce festival")
        if not festival.period.contains(slot):
            raise OutsideFestivalPeriod("Le concert doit se dérouler pendant le festival")
        if not stage.equipment.covers(artist.required_equipment):
            missing = ", ".join(sorted(stage.equipment.missing(artist.required_equipment)))
            raise MissingEquipment(f"La scène ne dispose pas des équipements requis : {missing}")
        for other in festival_concerts:
            if other.status is ConcertStatus.CANCELLED or other.id == exclude_concert_id:
                continue
            if not other.slot.overlaps(slot):
                continue
            if other.stage_id == stage.id:
                raise StageSlotConflict("Conflit : la scène est déjà occupée")
            if other.artist_id == artist.id:
                raise ArtistSlotConflict("Conflit : l'artiste est déjà programmé")
