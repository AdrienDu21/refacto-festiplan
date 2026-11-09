from datetime import datetime

import pytest

from app.domain.entities import Concert, ConcertStatus, Festival, PlanningStatus
from app.domain.errors import ConcertAlreadyCancelled, PlanningLocked, PlanningNotPublished
from app.domain.events import ConcertCancelled, ConcertRescheduled, PlanningPublished
from app.domain.value_objects import FestivalPeriod, TimeSlot


def slot(h1, h2):
    return TimeSlot(datetime(2027, 6, 18, h1), datetime(2027, 6, 18, h2))


def make_concert():
    return Concert(id=1, festival_id=1, artist_id=1, stage_id=1, slot=slot(18, 19))


def make_festival():
    period = FestivalPeriod(datetime(2027, 6, 18, 10), datetime(2027, 6, 20, 23))
    return Festival(id=1, name="Hellforge", location="Clisson", period=period)


def test_reschedule_changes_slot_and_records_event():
    concert = make_concert()
    concert.reschedule(slot(20, 21))
    assert concert.slot == slot(20, 21)
    assert concert.pull_events() == [ConcertRescheduled(1, 1, slot(18, 19), slot(20, 21))]


def test_pull_events_empties_the_list():
    concert = make_concert()
    concert.reschedule(slot(20, 21))
    concert.pull_events()
    assert concert.pull_events() == []


def test_cancelled_concert_cannot_be_rescheduled():
    concert = make_concert()
    concert.cancel()
    with pytest.raises(ConcertAlreadyCancelled):
        concert.reschedule(slot(20, 21))
    assert concert.slot == slot(18, 19)


def test_cancel_records_event_once():
    concert = make_concert()
    concert.cancel()
    concert.cancel()
    assert concert.status is ConcertStatus.CANCELLED
    assert concert.pull_events() == [ConcertCancelled(1, 1)]


def test_new_festival_is_in_preparation_and_editable():
    festival = make_festival()
    assert festival.status is PlanningStatus.PREPARATION
    festival.ensure_editable()


def test_publish_locks_the_planning_and_records_event():
    festival = make_festival()
    festival.publish()
    assert festival.is_published
    assert festival.pull_events() == [PlanningPublished(1)]
    with pytest.raises(PlanningLocked):
        festival.ensure_editable()


def test_cannot_publish_twice():
    festival = make_festival()
    festival.publish()
    with pytest.raises(PlanningLocked):
        festival.publish()


def test_unpublish_reopens_the_planning():
    festival = make_festival()
    festival.publish()
    festival.unpublish()
    assert festival.status is PlanningStatus.PREPARATION
    festival.ensure_editable()


def test_cannot_unpublish_a_planning_in_preparation():
    with pytest.raises(PlanningNotPublished):
        make_festival().unpublish()
