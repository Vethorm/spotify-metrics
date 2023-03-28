from dataclasses import asdict
from typing import List

from pymongo import DESCENDING, MongoClient, ReplaceOne
from tekore.model import PlayHistoryPaging

from .scraper_dataclasses import Artist, ArtistGenres, RecentlyPlayedMetric, TrackEnergy


class SpotifyMetricsDB:
    def __init__(self, username: str, password: str, host: str):
        self.client = MongoClient(f"mongodb://{username}:{password}@{host}:27017/")
        self.database = self.client["spotify_metrics"]
        self.collection_play_history = self.database["play_history"]
        self.collection_artist_genres = self.database["artist_genres"]
        self.collection_track_energy = self.database["track_energy"]

    def get_last_played_at(self) -> int:
        """Get the timestamp of the last played song

        Returns:
            int: last played timestamp in millisecond epoch
        """
        result = (
            self.collection_play_history.find().sort("played_at", DESCENDING).limit(1)
        )
        for played in result:
            last_played_at = played["played_at"]
            millisecond_epoch = int(last_played_at.timestamp() * 1000)
            print("Last played:", millisecond_epoch)
            return millisecond_epoch
        # probably should think of a more elegant solution to an empty database
        return 0

    def upsert_play_history(self, history: PlayHistoryPaging) -> None:
        """Upsert the play history to mongodb
        Args:
            history (PlayHistoryPaging): history object of recently played songs
        """
        metrics: List[RecentlyPlayedMetric] = []
        for track in history.items:
            artists = [Artist(artist.id, artist.name) for artist in track.track.artists]
            metrics.append(
                RecentlyPlayedMetric(
                    track.played_at,
                    track.track.name,
                    track.track.id,
                    artists,
                    track.track.popularity,
                )
            )
        requests = []
        for metric in metrics:
            replace = ReplaceOne(
                filter={"played_at": metric.played_at},
                replacement=asdict(metric),
                upsert=True,
            )
            requests.append(replace)
        self.collection_play_history.bulk_write(requests=requests)

    def upsert_artist_genres(self, artists: List[ArtistGenres]) -> None:
        """Upsert the artist genres to mongodb

        Args:
            artists (List[ArtistGenres]): list of artist genre objects to upsert
        """
        requests = []
        for artist in artists:
            replace = ReplaceOne(
                filter={"artist_id": artist.id}, replacement=asdict(artist), upsert=True
            )
            requests.append(replace)
        self.collection_artist_genres.bulk_write(requests)

    def upsert_track_energy(self, tracks: List[TrackEnergy]) -> None:
        """Upsert the track energies to mongodb

        Args:
            tracks (List[TrackEnergy]): list of track energy objects to upsert
        """
        requests = []
        for track in tracks:
            replace = ReplaceOne(
                filter={"track_id": track.id}, replacement=asdict(track), upsert=True
            )
            requests.append(replace)
        self.collection_track_energy.bulk_write(requests)
