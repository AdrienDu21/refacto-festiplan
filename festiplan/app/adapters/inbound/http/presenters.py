def concert_out(concert) -> dict:
    return {
        "id": concert.id,
        "festival_id": concert.festival_id,
        "artist_id": concert.artist_id,
        "stage_id": concert.stage_id,
        "start_time": concert.slot.start,
        "end_time": concert.slot.end,
        "status": concert.status.value,
    }


def festival_out(festival) -> dict:
    return {
        "id": festival.id,
        "name": festival.name,
        "location": festival.location,
        "start_date": festival.period.start,
        "end_date": festival.period.end,
        "status": festival.status.value,
    }


def stage_out(stage) -> dict:
    return {
        "id": stage.id,
        "festival_id": stage.festival_id,
        "name": stage.name,
        "capacity": stage.capacity.value,
        "available_equipment": sorted(stage.equipment.items),
    }


def artist_out(artist) -> dict:
    return {
        "id": artist.id,
        "name": artist.name,
        "genre": artist.genre,
        "required_equipment": sorted(artist.required_equipment.items),
    }


def incident_out(incident) -> dict:
    return {
        "id": incident.id,
        "concert_id": incident.concert_id,
        "description": incident.description,
        "occurred_at": incident.occurred_at,
        "resolved": incident.resolved,
    }
