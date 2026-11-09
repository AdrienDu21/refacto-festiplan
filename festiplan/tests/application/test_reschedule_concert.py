import pytest

from app.application.errors import EntityNotFound
from app.application.reschedule_concert import RescheduleConcert, RescheduleConcertCommand
from app.domain.errors import (
    ArtistSlotConflict,
    ConcertAlreadyCancelled,
    InvalidTimeSlot,
    MissingEquipment,
    OutsideFestivalPeriod,
    PlanningLocked,
    StageSlotConflict,
)
from app.domain.entities import Artist
from app.domain.events import ConcertRescheduled
from app.domain.value_objects import EquipmentSet
from fakes import FailingNotifier
from world import World, at, slot


def use_case(w):
    return RescheduleConcert(w.concerts, w.festivals, w.stages, w.artists, w.policy, w.notifier)


def reschedule(w, concert, h1, h2):
    return use_case(w).execute(RescheduleConcertCommand(concert.id, at(h1), at(h2)))


def test_valid_reschedule_is_saved_and_notified():
    w = World()
    reschedule(w, w.c2, 20, 21)
    assert w.concerts.get(w.c2.id).slot == slot(20, 21)
    assert w.notifier.events == [ConcertRescheduled(w.c2.id, w.festival.id, slot(19, 20), slot(20, 21))]


def test_same_stage_overlap_is_rejected_and_nothing_changes():
    w = World()
    with pytest.raises(StageSlotConflict):
        reschedule(w, w.c2, 18, 19)
    assert w.concerts.get(w.c2.id).slot == slot(19, 20)
    assert w.notifier.events == []


def test_same_artist_on_two_stages_is_rejected():
    w = World()
    with pytest.raises(ArtistSlotConflict):
        reschedule(w, w.c3, 19, 20)
    assert w.concerts.get(w.c3.id).slot == slot(21, 22)


def test_reschedule_on_published_planning_is_rejected():
    w = World()
    w.festival.publish()
    with pytest.raises(PlanningLocked):
        reschedule(w, w.c2, 20, 21)
    assert w.concerts.get(w.c2.id).slot == slot(19, 20)
    assert w.notifier.events == []


def test_reschedule_after_unpublish_is_accepted():
    w = World()
    w.festival.publish()
    w.festival.unpublish()
    reschedule(w, w.c2, 20, 21)
    assert w.concerts.get(w.c2.id).slot == slot(20, 21)


def test_notification_failure_does_not_fail_the_reschedule():
    notifier = FailingNotifier()
    w = World(notifier)
    concert = reschedule(w, w.c2, 20, 21)
    assert notifier.attempts == 1
    assert concert.slot == slot(20, 21)
    assert w.concerts.get(w.c2.id).slot == slot(20, 21)


def test_slot_outside_festival_is_rejected():
    w = World()
    with pytest.raises(OutsideFestivalPeriod):
        reschedule(w, w.c2, 1, 2)


def test_missing_equipment_is_rejected():
    w = World()
    needy = w.artists.add(Artist(None, "Needy", "Metal", EquipmentSet.of(["rigging"])))
    concert = w.add_concert(needy, w.main, slot(22, 23))
    with pytest.raises(MissingEquipment):
        reschedule(w, concert, 20, 21)


def test_invalid_slot_is_rejected():
    w = World()
    with pytest.raises(InvalidTimeSlot):
        reschedule(w, w.c2, 21, 20)


def test_unknown_concert_is_reported():
    w = World()
    with pytest.raises(EntityNotFound):
        use_case(w).execute(RescheduleConcertCommand(999, at(20), at(21)))


def test_cancelled_concert_cannot_be_rescheduled():
    w = World()
    w.c2.cancel()
    with pytest.raises(ConcertAlreadyCancelled):
        reschedule(w, w.c2, 20, 21)
