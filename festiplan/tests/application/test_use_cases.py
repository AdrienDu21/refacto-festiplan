import pytest

from app.application.cancel_concert import CancelConcert
from app.application.catalog import (
    CreateArtist,
    CreateArtistCommand,
    CreateFestival,
    CreateFestivalCommand,
    CreateStage,
    CreateStageCommand,
)
from app.application.errors import EntityNotFound, ReferenceNotFound
from app.application.incidents import ListIncidents, ReportIncident, ReportIncidentCommand
from app.application.planning import PublishPlanning, UnpublishPlanning
from app.application.queries import GetConcert, ListSchedule
from app.application.schedule_concert import ScheduleConcert, ScheduleConcertCommand
from app.domain.entities import Artist, ConcertStatus, PlanningStatus
from app.domain.errors import (
    ArtistSlotConflict,
    InvalidCapacity,
    InvalidFestivalPeriod,
    InvalidIncident,
    InvalidTimeSlot,
    MissingEquipment,
    OutsideFestivalPeriod,
    PlanningLocked,
    PlanningNotPublished,
    StageSlotConflict,
)
from app.domain.events import ConcertCancelled, PlanningPublished
from app.domain.value_objects import EquipmentSet
from fakes import FailingNotifier
from world import World, at, slot


def schedule(w, artist, stage, h1, h2, festival_id=None):
    use_case = ScheduleConcert(w.concerts, w.festivals, w.stages, w.artists, w.policy)
    return use_case.execute(
        ScheduleConcertCommand(festival_id or w.festival.id, artist.id, stage.id, at(h1), at(h2))
    )


def publish(w):
    return PublishPlanning(w.festivals, w.concerts, w.stages, w.artists, w.policy, w.notifier).execute(w.festival.id)


def cancel(w, concert):
    return CancelConcert(w.concerts, w.festivals, w.notifier).execute(concert.id)


def test_schedule_valid_concert_is_saved():
    w = World()
    concert = schedule(w, w.artist_a, w.side, 12, 13)
    assert concert.id is not None
    assert w.concerts.get(concert.id).slot == slot(12, 13)


def test_schedule_rejects_stage_overlap():
    w = World()
    with pytest.raises(StageSlotConflict):
        schedule(w, w.artist_a, w.main, 18, 19)


def test_schedule_rejects_artist_overlap():
    w = World()
    with pytest.raises(ArtistSlotConflict):
        schedule(w, w.artist_a, w.side, 18, 19)


def test_schedule_rejects_invalid_slot():
    w = World()
    with pytest.raises(InvalidTimeSlot):
        schedule(w, w.artist_a, w.side, 13, 12)


def test_schedule_rejects_slot_outside_festival():
    w = World()
    with pytest.raises(OutsideFestivalPeriod):
        schedule(w, w.artist_a, w.side, 1, 2)


def test_schedule_rejects_unknown_references():
    w = World()
    with pytest.raises(ReferenceNotFound):
        schedule(w, w.artist_a, w.side, 12, 13, festival_id=999)


def test_schedule_rejects_missing_equipment():
    w = World()
    needy = w.artists.add(Artist(None, "Needy", "Metal", EquipmentSet.of(["rigging"])))
    with pytest.raises(MissingEquipment):
        schedule(w, needy, w.main, 12, 13)


def test_schedule_is_refused_on_published_planning():
    w = World()
    publish(w)
    with pytest.raises(PlanningLocked):
        schedule(w, w.artist_a, w.side, 12, 13)


def test_cancel_marks_concert_cancelled_and_notifies():
    w = World()
    cancel(w, w.c1)
    assert w.concerts.get(w.c1.id).status is ConcertStatus.CANCELLED
    assert w.notifier.events == [ConcertCancelled(w.c1.id, w.festival.id)]


def test_cancel_frees_the_slot():
    w = World()
    cancel(w, w.c1)
    schedule(w, w.artist_b, w.main, 18, 19)


def test_cancel_unknown_concert_is_reported():
    w = World()
    with pytest.raises(EntityNotFound):
        CancelConcert(w.concerts, w.festivals, w.notifier).execute(999)


def test_cancel_is_refused_on_published_planning():
    w = World()
    publish(w)
    with pytest.raises(PlanningLocked):
        cancel(w, w.c1)
    assert w.concerts.get(w.c1.id).status is ConcertStatus.SCHEDULED


def test_cancel_survives_notification_failure():
    w = World(FailingNotifier())
    cancel(w, w.c1)
    assert w.concerts.get(w.c1.id).status is ConcertStatus.CANCELLED


def test_publish_valid_planning():
    w = World()
    festival = publish(w)
    assert festival.status is PlanningStatus.PUBLISHED
    assert w.festivals.get(w.festival.id).is_published
    assert w.notifier.events == [PlanningPublished(w.festival.id)]


def test_publish_empty_planning_is_accepted():
    w = World()
    for concert in (w.c1, w.c2, w.c3):
        concert.cancel()
    assert publish(w).is_published


def test_publish_refuses_planning_with_conflicts():
    w = World()
    w.add_concert(w.artist_a, w.main, slot(18, 19))
    with pytest.raises(StageSlotConflict):
        publish(w)
    assert not w.festivals.get(w.festival.id).is_published
    assert w.notifier.events == []


def test_publish_twice_is_refused():
    w = World()
    publish(w)
    with pytest.raises(PlanningLocked):
        publish(w)


def test_publish_unknown_festival_is_reported():
    w = World()
    with pytest.raises(EntityNotFound):
        PublishPlanning(w.festivals, w.concerts, w.stages, w.artists, w.policy, w.notifier).execute(999)


def test_publish_survives_notification_failure():
    w = World(FailingNotifier())
    assert publish(w).is_published
    assert w.festivals.get(w.festival.id).is_published


def test_unpublish_reopens_the_planning():
    w = World()
    publish(w)
    UnpublishPlanning(w.festivals).execute(w.festival.id)
    assert not w.festivals.get(w.festival.id).is_published
    schedule(w, w.artist_a, w.side, 12, 13)


def test_unpublish_requires_a_published_planning():
    w = World()
    with pytest.raises(PlanningNotPublished):
        UnpublishPlanning(w.festivals).execute(w.festival.id)


def test_report_incident():
    w = World()
    use_case = ReportIncident(w.concerts, w.incidents, clock=lambda: at(22))
    incident = use_case.execute(ReportIncidentCommand(w.c1.id, "  Panne de courant "))
    assert incident.id is not None
    assert incident.description == "Panne de courant"
    assert incident.occurred_at == at(22)


def test_report_incident_uses_given_date():
    w = World()
    incident = ReportIncident(w.concerts, w.incidents).execute(ReportIncidentCommand(w.c1.id, "Panne", at(20)))
    assert incident.occurred_at == at(20)


def test_report_incident_requires_a_description():
    w = World()
    with pytest.raises(InvalidIncident):
        ReportIncident(w.concerts, w.incidents).execute(ReportIncidentCommand(w.c1.id, "   "))
    assert w.incidents.list() == []


def test_report_incident_requires_an_existing_concert():
    w = World()
    with pytest.raises(EntityNotFound):
        ReportIncident(w.concerts, w.incidents).execute(ReportIncidentCommand(999, "Panne"))


def test_incidents_are_listed_by_concert_most_recent_first():
    w = World()
    report = ReportIncident(w.concerts, w.incidents)
    first = report.execute(ReportIncidentCommand(w.c1.id, "Premier", at(18)))
    second = report.execute(ReportIncidentCommand(w.c1.id, "Second", at(19)))
    report.execute(ReportIncidentCommand(w.c2.id, "Autre", at(20)))
    listed = ListIncidents(w.incidents).execute(w.c1.id)
    assert [i.id for i in listed] == [second.id, first.id]
    assert len(ListIncidents(w.incidents).execute()) == 3


def test_create_festival_validates_period():
    w = World()
    with pytest.raises(InvalidFestivalPeriod):
        CreateFestival(w.festivals).execute(CreateFestivalCommand("F", "L", at(10, day=20), at(10, day=19)))


def test_create_stage_requires_positive_capacity():
    w = World()
    with pytest.raises(InvalidCapacity):
        CreateStage(w.festivals, w.stages).execute(CreateStageCommand(w.festival.id, "Stage", 0))


def test_create_stage_requires_existing_festival():
    w = World()
    with pytest.raises(ReferenceNotFound):
        CreateStage(w.festivals, w.stages).execute(CreateStageCommand(999, "Stage", 100))


def test_create_stage_and_artist_keep_equipment():
    w = World()
    stage = CreateStage(w.festivals, w.stages).execute(CreateStageCommand(w.festival.id, "New", 100, ["lights"]))
    artist = CreateArtist(w.artists).execute(CreateArtistCommand("New", "Doom", ["lights", " "]))
    assert stage.equipment.items == frozenset({"lights"})
    assert artist.required_equipment.items == frozenset({"lights"})


def test_schedule_listing_excludes_cancelled_and_is_chronological():
    w = World()
    cancel(w, w.c1)
    listed = ListSchedule(w.concerts).execute(w.festival.id)
    assert [c.id for c in listed] == [w.c2.id, w.c3.id]


def test_get_concert():
    w = World()
    assert GetConcert(w.concerts).execute(w.c1.id).id == w.c1.id
    with pytest.raises(EntityNotFound):
        GetConcert(w.concerts).execute(999)
