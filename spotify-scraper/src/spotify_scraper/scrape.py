import tekore as tk
from tekore import Spotify, RefreshingCredentials
from tekore.model import PlayHistoryPaging, FullArtist, AudioFeatures

from typing import List, Optional
from .scraper_dataclasses import ArtistGenres, TrackEnergy

from functools import wraps

import os

conf = tk.config_from_environment(True)
client_id, client_secret, redirect_uri, user_refresh = conf
spotify = tk.Spotify(user_refresh, chunked_on=True)
credentials = tk.Credentials(client_id, client_secret)


def refresh(func):
    """decorator to refresh a token before doing an API call"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        refresh_token()
        return func(*args, **kwargs)

    return wrapper


@refresh
def get_recently_played(
    client: Spotify, limit: int = 50, after: Optional[int] = None
) -> PlayHistoryPaging:
    """Get the recently played song history.
        Only the 50 most recently played songs can ever be collected. This is
        a limitation of the Spotify API.

    Args:
        client (Spotify): spotify client to use
        limit (int, optional): optional song limit. Defaults to 50
        after (int, optional): millisecond epoch timestamp to use as lower
            bound for our recently played songs

    Returns:
        PlayHistoryPaging
    """
    if after:
        history = client.playback_recently_played(limit=limit, after=after)
    else:
        history = client.playback_recently_played(limit=limit)
    return history


def extract_artist_ids_from_history(history: PlayHistoryPaging) -> List[str]:
    """Extract the artist ids from the listen history

    Args:
        history (PlayHistoryPaging): the listen history we extract from

    Returns:
        List[str]: list of artist ids
    """
    artist_ids = []
    for track in history.items:
        for artist in track.track.artists:
            artist_ids.append(artist.id)
    return artist_ids


def extract_track_ids_from_history(history: PlayHistoryPaging) -> List[str]:
    """Extract the track ids from the listen history

    Args:
        history (PlayHistoryPaging): the listen history we extract from

    Returns:
        List[str]: list of track ids
    """
    return [track.track.id for track in history.items]


def get_artists(client: Spotify, artist_ids: List[str]) -> List[FullArtist]:
    """Get the artist data for a list of artist ids

    Args:
        client (Spotify): the spotify client to use
        artist_ids (List[str]): the list of artist ids to get

    Returns:
        List[FullArtist]: list of the full artist data objects
    """
    artists = client.artists(artist_ids)
    return artists


def extract_artist_genres(artists: List[FullArtist]) -> List[ArtistGenres]:
    """Extract the artist genres from a list of artists

    Args:
        artists (List[FullArtist]): list of artists we use to extract genres

    Returns:
        List[ArtistGenres]: list of ArtistGenres objects
    """
    return [ArtistGenres(artist.id, artist.genres) for artist in artists]


def get_audio_features(client: Spotify, track_ids: List[str]) -> List[AudioFeatures]:
    """Gets the audio features for a list of track ids from the Spotify API
    Args:
        client (Spotify): the spotify client to use
        track_ids List[str]: list of track ids to get audio features for

    Returns:
        List[AudioFeatures]: list of audio features
    """
    audio_features = client.tracks_audio_features(track_ids)
    return audio_features


def extract_track_energies(tracks: List[AudioFeatures]) -> List[TrackEnergy]:
    """Extract the energy of the provided tracks

    Args:
        tracks (List[AudioFeatures]): list of tracks to extract from

    Returns:
        List[TrackEnergy]: list of track energy objects
    """
    return [TrackEnergy(track.id, track.energy) for track in tracks]


def get_new_token():
    refresh_token = tk.prompt_for_user_token(
        client_id, client_secret, redirect_uri, tk.scope.every
    )
    # print("Access token\n", refresh_token.access_token)
    print("Refresh token\n", refresh_token.refresh_token)


def refresh_token():
    """Refresh the token for the spotify client"""
    global spotify
    print("Refreshing user token")
    refresh_token = os.environ["SPOTIFY_REFRESH_TOKEN"]
    refreshing_credentials = RefreshingCredentials(client_id, client_secret)
    refreshing_token = refreshing_credentials.refresh_user_token(refresh_token)
    spotify = tk.Spotify(refreshing_token.access_token, chunked_on=True)
