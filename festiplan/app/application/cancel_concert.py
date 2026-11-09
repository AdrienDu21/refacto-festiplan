from app.application.errors import EntityNotFound
from app.application.event_dispatch import dispatch_events
from app.application.ports import ConcertRepository, FestivalRepository, NotificationPort
from app.domain.entities import Concert


class CancelConcert:
    def __init__(self, concerts: ConcertRepository, festivals: FestivalRepository, notifier: NotificationPort):
        self._concerts = concerts
        self._festivals = festivals
        self._notifier = notifier

    def execute(self, concert_id: int) -> Concert:
        concert = self._concerts.get(concert_id)
        if concert is None:
            raise EntityNotFound("Concert", concert_id)
        self._festivals.get(concert.festival_id).ensure_editable()
        concert.cancel()
        self._concerts.save(concert)
        dispatch_events(concert.pull_events(), self._notifier)
        return concert
