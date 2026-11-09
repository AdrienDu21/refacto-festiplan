from fastapi import APIRouter, Depends

from app.adapters.inbound.http.presenters import artist_out
from app.adapters.inbound.http.schemas import ArtistCreate, ArtistRead
from app.application.catalog import CreateArtist, CreateArtistCommand
from app.application.queries import ListArtists
from app.composition import get_create_artist, get_list_artists

router = APIRouter(prefix="/artists", tags=["artists"])


@router.get("", response_model=list[ArtistRead])
def list_artists(use_case: ListArtists = Depends(get_list_artists)):
    return [artist_out(a) for a in use_case.execute()]


@router.post("", response_model=ArtistRead, status_code=201)
def create_artist(payload: ArtistCreate, use_case: CreateArtist = Depends(get_create_artist)):
    command = CreateArtistCommand(payload.name, payload.genre, payload.required_equipment)
    return artist_out(use_case.execute(command))
