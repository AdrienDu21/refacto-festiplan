from datetime import datetime

import pytest

from app.adapters.outbound.notification import email_notifier
from app.adapters.outbound.notification.email_notifier import EmailNotifier
from app.config import settings
from app.domain.events import ConcertCancelled, ConcertRescheduled, PlanningPublished
from app.domain.value_objects import TimeSlot


def slot(h1, h2):
    return TimeSlot(datetime(2027, 6, 18, h1), datetime(2027, 6, 18, h2))


@pytest.fixture
def sent(monkeypatch):
    calls = []
    monkeypatch.setattr(email_notifier, "send_email", lambda to, subject, body: calls.append((to, subject, body)))
    return calls


def test_rescheduled_event_sends_an_email(sent):
    EmailNotifier().notify(ConcertRescheduled(4, 1, slot(18, 19), slot(20, 21)))
    assert len(sent) == 1
    assert "#4" in sent[0][1]
    assert "2027-06-18T20:00:00" in sent[0][2]


def test_cancelled_event_sends_an_email(sent):
    EmailNotifier().notify(ConcertCancelled(4, 1))
    assert "Annulation" in sent[0][1]


def test_published_event_sends_an_email(sent):
    EmailNotifier().notify(PlanningPublished(1))
    assert "Publication" in sent[0][1]


def test_unknown_event_sends_nothing(sent):
    EmailNotifier().notify(object())
    assert sent == []


def test_notifier_propagates_sender_failure(monkeypatch):
    monkeypatch.setattr(settings, "fail_notifications", True)
    with pytest.raises(RuntimeError):
        EmailNotifier().notify(ConcertCancelled(4, 1))
