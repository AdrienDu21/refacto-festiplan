from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.outbound.notification.email_notifier import EmailNotifier
from app.adapters.outbound.persistence.database import get_db
from app.adapters.outbound.persistence.sql_repositories import (
    SqlArtistRepository,
    SqlConcertRepository,
    SqlFestivalRepository,
    SqlIncidentRepository,
    SqlStageRepository,
)
from app.application.cancel_concert import CancelConcert
from app.application.catalog import CreateArtist, CreateFestival, CreateStage
from app.application.incidents import ListIncidents, ReportIncident
from app.application.planning import PublishPlanning, UnpublishPlanning
from app.application.queries import GetConcert, ListArtists, ListFestivals, ListSchedule, ListStages
from app.application.reschedule_concert import RescheduleConcert
from app.application.schedule_concert import ScheduleConcert
from app.domain.policies import SchedulingPolicy


def get_schedule_concert(db: Session = Depends(get_db)) -> ScheduleConcert:
    return ScheduleConcert(
        SqlConcertRepository(db),
        SqlFestivalRepository(db),
        SqlStageRepository(db),
        SqlArtistRepository(db),
        SchedulingPolicy(),
    )


def get_reschedule_concert(db: Session = Depends(get_db)) -> RescheduleConcert:
    return RescheduleConcert(
        SqlConcertRepository(db),
        SqlFestivalRepository(db),
        SqlStageRepository(db),
        SqlArtistRepository(db),
        SchedulingPolicy(),
        EmailNotifier(),
    )


def get_cancel_concert(db: Session = Depends(get_db)) -> CancelConcert:
    return CancelConcert(SqlConcertRepository(db), SqlFestivalRepository(db), EmailNotifier())


def get_publish_planning(db: Session = Depends(get_db)) -> PublishPlanning:
    return PublishPlanning(
        SqlFestivalRepository(db),
        SqlConcertRepository(db),
        SqlStageRepository(db),
        SqlArtistRepository(db),
        SchedulingPolicy(),
        EmailNotifier(),
    )


def get_unpublish_planning(db: Session = Depends(get_db)) -> UnpublishPlanning:
    return UnpublishPlanning(SqlFestivalRepository(db))


def get_report_incident(db: Session = Depends(get_db)) -> ReportIncident:
    return ReportIncident(SqlConcertRepository(db), SqlIncidentRepository(db))


def get_list_incidents(db: Session = Depends(get_db)) -> ListIncidents:
    return ListIncidents(SqlIncidentRepository(db))


def get_create_festival(db: Session = Depends(get_db)) -> CreateFestival:
    return CreateFestival(SqlFestivalRepository(db))


def get_create_stage(db: Session = Depends(get_db)) -> CreateStage:
    return CreateStage(SqlFestivalRepository(db), SqlStageRepository(db))


def get_create_artist(db: Session = Depends(get_db)) -> CreateArtist:
    return CreateArtist(SqlArtistRepository(db))


def get_list_festivals(db: Session = Depends(get_db)) -> ListFestivals:
    return ListFestivals(SqlFestivalRepository(db))


def get_list_artists(db: Session = Depends(get_db)) -> ListArtists:
    return ListArtists(SqlArtistRepository(db))


def get_list_stages(db: Session = Depends(get_db)) -> ListStages:
    return ListStages(SqlStageRepository(db))


def get_concert(db: Session = Depends(get_db)) -> GetConcert:
    return GetConcert(SqlConcertRepository(db))


def get_list_schedule(db: Session = Depends(get_db)) -> ListSchedule:
    return ListSchedule(SqlConcertRepository(db))
