import os
import time
from functools import wraps
from typing import List, Optional

import tekore as tk
from tekore import RefreshingCredentials
from tekore.model import AudioFeatures, FullArtist, PlayHistoryPaging

from spotify_scraper.database import SpotifyMetricsDB
from spotify_scraper.models.track import Track, TrackFeatures
from spotify_scraper.models.artist import Artist
from .logger import logger


class SpotifyScraper:
    def __init__(self, client_id, client_secret, redirect_uri, user_refresh):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.user_refresh = user_refresh
        self.client = tk.Spotify(self.user_refresh, chunked_on=True)

    def refresh(func):
        """decorator to refresh a token before doing an API call"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.client.token = refresh_token(self.client_id, self.client_secret)
            return func(self, *args, **kwargs)

        return wrapper

    @refresh
    def get_recently_played(
        self, limit: int = 50, after: Optional[int] = None
    ) -> PlayHistoryPaging:
        """Get the recently played song history.
            Only the 50 most recently played songs can ever be collected. This is
            a limitation of the Spotify API.

        Args:
            limit (int, optional): optional song limit. Defaults to 50
            after (int, optional): millisecond epoch timestamp to use as lower
                bound for our recently played songs

        Returns:
            PlayHistoryPaging
        """
        if after:
            history = self.client.playback_recently_played(limit=limit, after=after)
        else:
            history = self.client.playback_recently_played(limit=limit)
        return history

    def extract_tracks(self, history: PlayHistoryPaging) -> List[Track]:
        tracks = []
        for track in history.items:
            tracks.append(
                Track(
                    track_id=track.track.id,
                    artist_ids=[artist.id for artist in track.track.artists],
                    popularity=track.track.popularity,
                )
            )
        return tracks

    def extract_artist_ids_from_history(self, history: PlayHistoryPaging) -> List[str]:
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

    def extract_track_ids_from_history(self, history: PlayHistoryPaging) -> List[str]:
        """Extract the track ids from the listen history

        Args:
            history (PlayHistoryPaging): the listen history we extract from

        Returns:
            List[str]: list of track ids
        """
        return [track.track.id for track in history.items]

    def get_artists(self, artist_ids: List[str]) -> List[FullArtist]:
        """Get the artist data for a list of artist ids

        Args:
            artist_ids (List[str]): the list of artist ids to get

        Returns:
            List[FullArtist]: list of the full artist data objects
        """
        artists = self.client.artists(artist_ids)
        return artists

    def extract_artists(self, artists: List[FullArtist]) -> List[Artist]:
        """Extract the artist genres from a list of artists

        Args:
            artists (List[FullArtist]): list of artists we use to extract genres

        Returns:
            List[ArtistGenres]: list of ArtistGenres objects
        """
        return [
            Artist(
                artist_id=artist.id,
                artist_name=artist.name,
                genres=artist.genres,
                popularity=artist.popularity,
            )
            for artist in artists
        ]

    def get_audio_features(self, track_ids: List[str]) -> List[AudioFeatures]:
        """Gets the audio features for a list of track ids from the Spotify API
        Args:
            track_ids List[str]: list of track ids to get audio features for

        Returns:
            List[AudioFeatures]: list of audio features
        """
        audio_features = self.client.tracks_audio_features(track_ids)
        return audio_features

    def extract_track_features(
        self, tracks: List[AudioFeatures]
    ) -> List[TrackFeatures]:
        """Extract the energy of the provided tracks

        Args:
            tracks (List[AudioFeatures]): list of tracks to extract from

        Returns:
            List[TrackEnergy]: list of track energy objects
        """
        return [
            TrackFeatures(
                track_id=track.id,
                acousticness=track.acousticness,
                danceability=track.danceability,
                duration_ms=track.duration_ms,
                energy=track.energy,
                instrumentalness=track.instrumentalness,
                key=track.key,
                liveness=track.liveness,
                loudness=track.loudness,
                mode=track.mode,
                speechiness=track.speechiness,
                tempo=track.tempo,
                time_signature=track.time_signature,
                type=track.type,
                valence=track.valence,
            )
            for track in tracks
        ]


def get_new_token(client_id, client_secret, redirect_uri) -> None:
    """Prints a new refresh token for a user

    Args:
        client_id: client id value for api
        client_secret: client secret value api
        redirect_uri: the redirect uri you configured for the api
    """
    refresh_token = tk.prompt_for_user_token(
        client_id, client_secret, redirect_uri, tk.scope.every
    )
    # print("Access token\n", refresh_token.access_token)
    print("Refresh token\n", refresh_token.refresh_token)


def refresh_token(client_id, client_secret) -> str:
    """Refreshes a spotify token and initializes a new Spotify client

    Args:
        client_id: client id value for api
        client_secret: client secret value api

    Returns:
        Spotify: the new spotify client
    """
    logger.info("Refreshing user token")
    refresh_token = os.environ["SPOTIFY_REFRESH_TOKEN"]
    refreshing_credentials = RefreshingCredentials(client_id, client_secret)
    refreshing_token = refreshing_credentials.refresh_user_token(refresh_token)
    return refreshing_token.access_token


def refresh_data() -> None:
    """Run the script to scrape data from the spotify API for recently played
    history metrics
    """
    logger.info("Beginning scrape worker")
    conf = tk.config_from_environment(True)
    # username = os.environ["MONGO_USER"]
    # password = os.environ["MONGO_PASS"]
    # host = os.environ["MONGO_HOST"]
    metrics_db = SpotifyMetricsDB()
    client_id, client_secret, redirect_uri, user_refresh = conf
    spotify_scraper = SpotifyScraper(*conf)

    spotify_scraper.client.token = refresh_token(client_id, client_secret)

    minutes = 1

    while True:
        last_played = metrics_db.get_last_played_at()
        history = spotify_scraper.get_recently_played(after=last_played)
        if len(history.items) == 0:
            logger.info(f"Processing history: len={len(history.items)}")
        else:
            logger.info(
                (
                    f"Processing history: len={len(history.items)},",
                    f"after={history.cursors.after},",
                    f"before={history.cursors.before}",
                )
            )
            metrics_db.upsert_play_history(history)

            tracks: List[Track]
            tracks = spotify_scraper.extract_tracks(history)
            metrics_db.upsert_track(tracks)

            track_features: List[TrackFeatures]
            track_ids = spotify_scraper.extract_track_ids_from_history(history)
            audio_features = spotify_scraper.get_audio_features(track_ids)
            track_features = spotify_scraper.extract_track_features(audio_features)
            metrics_db.upsert_track_features(track_features)

            artists: List[Artist]
            artist_ids = spotify_scraper.extract_artist_ids_from_history(history)
            artists = spotify_scraper.get_artists(artist_ids)
            artists = spotify_scraper.extract_artists(artists)
            metrics_db.upsert_artist(artists)

        logger.info(f"Sleeping for {60 * minutes}")
        time.sleep(60 * minutes)
