from datetime import datetime

import pytest

from app.domain.errors import InvalidCapacity, InvalidFestivalPeriod, InvalidTimeSlot
from app.domain.value_objects import Capacity, EquipmentSet, FestivalPeriod, TimeSlot


def t(hour, minute=0, day=18):
    return datetime(2027, 6, day, hour, minute)


def slot(h1, h2):
    return TimeSlot(t(h1), t(h2))



def test_slot_end_must_be_after_start():
    with pytest.raises(InvalidTimeSlot):
        TimeSlot(t(19), t(18))


def test_slot_with_zero_duration_is_invalid():
    with pytest.raises(InvalidTimeSlot):
        TimeSlot(t(18), t(18))


def test_slot_is_immutable():
    s = slot(18, 19)
    with pytest.raises(Exception):
        s.start = t(10)


def test_overlapping_slots():
    assert slot(18, 20).overlaps(slot(19, 21))
    assert slot(19, 21).overlaps(slot(18, 20))


def test_contained_slot_overlaps():
    assert slot(18, 22).overlaps(slot(19, 20))


def test_identical_slots_overlap():
    assert slot(18, 19).overlaps(slot(18, 19))


def test_adjacent_slots_do_not_overlap():
    assert not slot(18, 19).overlaps(slot(19, 20))
    assert not slot(19, 20).overlaps(slot(18, 19))


def test_distant_slots_do_not_overlap():
    assert not slot(10, 11).overlaps(slot(18, 19))



def test_period_end_must_be_after_start():
    with pytest.raises(InvalidFestivalPeriod):
        FestivalPeriod(t(10, day=20), t(10, day=19))


def test_period_contains_slot():
    period = FestivalPeriod(t(10, day=18), t(23, day=20))
    assert period.contains(slot(18, 19))


def test_period_contains_slot_touching_bounds():
    period = FestivalPeriod(t(10), t(22))
    assert period.contains(slot(10, 22))


def test_period_does_not_contain_slot_starting_before():
    period = FestivalPeriod(t(10), t(22))
    assert not period.contains(slot(9, 11))


def test_period_does_not_contain_slot_ending_after():
    period = FestivalPeriod(t(10), t(22))
    assert not period.contains(slot(21, 23))



def test_stage_covers_required_equipment():
    stage = EquipmentSet.of(["lights", "rigging", "pyro"])
    assert stage.covers(EquipmentSet.of(["lights", "rigging"]))


def test_stage_missing_equipment_is_not_covered():
    stage = EquipmentSet.of(["lights"])
    required = EquipmentSet.of(["lights", "rigging"])
    assert not stage.covers(required)
    assert stage.missing(required) == frozenset({"rigging"})


def test_no_requirement_is_always_covered():
    assert EquipmentSet.of([]).covers(EquipmentSet.of([]))


def test_equipment_is_normalized():
    assert EquipmentSet.of([" lights ", "", "lights"]).items == frozenset({"lights"})



@pytest.mark.parametrize("value", [0, -1, -5000])
def test_capacity_must_be_positive(value):
    with pytest.raises(InvalidCapacity):
        Capacity(value)


def test_valid_capacity():
    assert Capacity(1).value == 1
