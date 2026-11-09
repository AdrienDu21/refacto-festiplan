import logging
from typing import Iterable

from app.application.ports import NotificationPort

logger = logging.getLogger(__name__)


def dispatch_events(events: Iterable, notifier: NotificationPort) -> None:
    for event in events:
        try:
            notifier.notify(event)
        except Exception:
            logger.exception("Échec de la notification pour l'événement %s", event)
