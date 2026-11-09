class _InMemoryRepository:
    def __init__(self):
        self._items = {}
        self._next_id = 1

    def get(self, item_id):
        return self._items.get(item_id)

    def list(self):
        return list(self._items.values())

    def add(self, item):
        item.id = self._next_id
        self._next_id += 1
        self._items[item.id] = item
        return item

    def save(self, item):
        self._items[item.id] = item


class InMemoryConcertRepository(_InMemoryRepository):
    def list_for_festival(self, festival_id):
        return [c for c in self._items.values() if c.festival_id == festival_id]


class InMemoryFestivalRepository(_InMemoryRepository):
    pass


class InMemoryStageRepository(_InMemoryRepository):
    def list_for_festival(self, festival_id):
        return [s for s in self._items.values() if s.festival_id == festival_id]


class InMemoryArtistRepository(_InMemoryRepository):
    pass


class RecordingNotifier:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


class FailingNotifier:
    def __init__(self):
        self.attempts = 0

    def notify(self, event):
        self.attempts += 1
        raise RuntimeError("Simulation : le service de notification est indisponible")


class InMemoryIncidentRepository(_InMemoryRepository):
    def list(self, concert_id=None):
        items = [i for i in self._items.values() if concert_id is None or i.concert_id == concert_id]
        return sorted(items, key=lambda i: i.occurred_at, reverse=True)
