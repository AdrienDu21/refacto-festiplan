class DomainError(Exception):
    pass


class InvalidTimeSlot(DomainError):
    pass


class InvalidFestivalPeriod(DomainError):
    pass


class InvalidCapacity(DomainError):
    pass


class StageNotInFestival(DomainError):
    pass


class StageSlotConflict(DomainError):
    pass


class ArtistSlotConflict(DomainError):
    pass


class MissingEquipment(DomainError):
    pass


class OutsideFestivalPeriod(DomainError):
    pass


class PlanningLocked(DomainError):
    pass


class PlanningNotPublished(DomainError):
    pass


class InvalidIncident(DomainError):
    pass


class ConcertAlreadyCancelled(DomainError):
    pass
