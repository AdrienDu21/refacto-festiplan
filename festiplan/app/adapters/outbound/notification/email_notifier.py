from app.domain.events import ConcertCancelled, ConcertRescheduled, PlanningPublished
from app.adapters.outbound.notification.email_sender import send_email

RECIPIENT = "production@festiplan.test"


class EmailNotifier:
    def notify(self, event) -> None:
        if isinstance(event, ConcertRescheduled):
            send_email(
                RECIPIENT,
                f"Modification du concert #{event.concert_id}",
                f"Concert déplacé au {event.new_slot.start.isoformat()}",
            )
        elif isinstance(event, ConcertCancelled):
            send_email(RECIPIENT, f"Annulation du concert #{event.concert_id}", "Le concert a été annulé.")
        elif isinstance(event, PlanningPublished):
            send_email(
                RECIPIENT,
                f"Publication du planning du festival #{event.festival_id}",
                "Le planning a été publié.",
            )
