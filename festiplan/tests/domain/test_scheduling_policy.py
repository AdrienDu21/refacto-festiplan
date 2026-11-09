from datetime import datetime

import pytest

from app.domain.entities import Artist, Concert, Festival, Stage
from app.domain.errors import (
    ArtistSlotConflict,
    MissingEquipment,
    OutsideFestivalPeriod,
    PlanningLocked,
    StageNotInFestival,
    StageSlotConflict,
)
from app.domain.policies import SchedulingPolicy
from app.domain.value_objects import Capacity, EquipmentSet, FestivalPeriod, TimeSlot


def slot(h1, h2, day=18):
    return TimeSlot(datetime(2027, 6, day, h1), datetime(2027, 6, day, h2))


def make_festival():
    period = FestivalPeriod(datetime(2027, 6, 18, 10), datetime(2027, 6, 20, 23))
    return Festival(id=1, name="Hellforge", location="Clisson", period=period)


def make_stage(id=1, festival_id=1, equipment=()):
    return Stage(id, festival_id, f"Stage {id}", Capacity(1000), EquipmentSet.of(equipment))


def make_artist(id=1, required=()):
    return Artist(id, f"Artist {id}", "Metal", EquipmentSet.of(required))


def make_concert(id, artist_id, stage_id, s):
    return Concert(id=id, festival_id=1, artist_id=artist_id, stage_id=stage_id, slot=s)


@pytest.fixture
def policy():
    return SchedulingPolicy()


def test_valid_slot_is_accepted(policy):
    existing = [make_concert(1, 1, 1, slot(18, 19))]
    policy.check(make_festival(), make_stage(), make_artist(2), slot(20, 21), existing)


def test_adjacent_slot_on_same_stage_is_accepted(policy):
    existing = [make_concert(1, 1, 1, slot(18, 19))]
    policy.check(make_festival(), make_stage(), make_artist(2), slot(19, 20), existing)


def test_same_stage_overlap_is_rejected(policy):
    existing = [make_concert(1, 1, 1, slot(18, 19))]
    with pytest.raises(StageSlotConflict):
        policy.check(make_festival(), make_stage(), make_artist(2), slot(18, 20), existing)


def test_same_artist_on_another_stage_is_rejected(policy):
    existing = [make_concert(1, 1, 1, slot(18, 19))]
    with pytest.raises(ArtistSlotConflict):
        policy.check(make_festival(), make_stage(2), make_artist(1), slot(18, 19), existing)


def test_same_artist_on_another_stage_at_different_time_is_accepted(policy):
    existing = [make_concert(1, 1, 1, slot(18, 19))]
    policy.check(make_festival(), make_stage(2), make_artist(1), slot(20, 21), existing)


def test_overlap_on_another_stage_with_another_artist_is_accepted(policy):
    existing = [make_concert(1, 1, 1, slot(18, 19))]
    policy.check(make_festival(), make_stage(2), make_artist(2), slot(18, 19), existing)


def test_concert_being_moved_does_not_conflict_with_itself(policy):
    existing = [make_concert(1, 1, 1, slot(18, 19))]
    policy.check(make_festival(), make_stage(), make_artist(1), slot(18, 20), existing, exclude_concert_id=1)


def test_cancelled_concert_does_not_conflict(policy):
    cancelled = make_concert(1, 1, 1, slot(18, 19))
    cancelled.cancel()
    policy.check(make_festival(), make_stage(), make_artist(2), slot(18, 19), [cancelled])


def test_stage_from_another_festival_is_rejected(policy):
    with pytest.raises(StageNotInFestival):
        policy.check(make_festival(), make_stage(festival_id=2), make_artist(), slot(18, 19), [])


def test_slot_before_festival_is_rejected(policy):
    with pytest.raises(OutsideFestivalPeriod):
        policy.check(make_festival(), make_stage(), make_artist(), slot(8, 9), [])


def test_slot_after_festival_is_rejected(policy):
    with pytest.raises(OutsideFestivalPeriod):
        policy.check(make_festival(), make_stage(), make_artist(), slot(1, 2, day=21), [])


def test_missing_equipment_is_rejected(policy):
    stage = make_stage(equipment=["lights"])
    artist = make_artist(required=["lights", "rigging"])
    with pytest.raises(MissingEquipment, match="rigging"):
        policy.check(make_festival(), stage, artist, slot(18, 19), [])


def test_available_equipment_is_accepted(policy):
    stage = make_stage(equipment=["lights", "rigging"])
    artist = make_artist(required=["lights"])
    policy.check(make_festival(), stage, artist, slot(18, 19), [])


def test_published_planning_rejects_any_change(policy):
    festival = make_festival()
    festival.publish()
    with pytest.raises(PlanningLocked):
        policy.check(festival, make_stage(), make_artist(), slot(18, 19), [])


def test_valid_planning_passes_validation(policy):
    concerts = [make_concert(1, 1, 1, slot(18, 19)), make_concert(2, 2, 1, slot(20, 21))]
    stages = {1: make_stage()}
    artists = {1: make_artist(1), 2: make_artist(2)}
    policy.validate_planning(make_festival(), stages, artists, concerts)


def test_empty_planning_passes_validation(policy):
    policy.validate_planning(make_festival(), {}, {}, [])


def test_planning_with_conflict_fails_validation(policy):
    concerts = [make_concert(1, 1, 1, slot(18, 19)), make_concert(2, 2, 1, slot(18, 20))]
    stages = {1: make_stage()}
    artists = {1: make_artist(1), 2: make_artist(2)}
    with pytest.raises(StageSlotConflict):
        policy.validate_planning(make_festival(), stages, artists, concerts)


def test_planning_with_artist_conflict_fails_validation(policy):
    concerts = [make_concert(1, 1, 1, slot(18, 19)), make_concert(2, 1, 2, slot(18, 19))]
    stages = {1: make_stage(1), 2: make_stage(2)}
    artists = {1: make_artist(1)}
    with pytest.raises(ArtistSlotConflict):
        policy.validate_planning(make_festival(), stages, artists, concerts)


def test_cancelled_concerts_are_ignored_by_validation(policy):
    kept = make_concert(1, 1, 1, slot(18, 19))
    cancelled = make_concert(2, 2, 1, slot(18, 19))
    cancelled.cancel()
    stages = {1: make_stage()}
    artists = {1: make_artist(1), 2: make_artist(2)}
    policy.validate_planning(make_festival(), stages, artists, [kept, cancelled])
