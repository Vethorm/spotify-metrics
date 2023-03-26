from pymongo import MongoClient, ReplaceOne, DESCENDING
from tekore.model import PlayHistoryPaging

from dataclasses import asdict
from .scraper_dataclasses import RecentlyPlayedMetric, Artist, ArtistGenres, TrackEnergy

from typing import List

import os

import time

mongo_user = os.environ["MONGO_USER"]
mongo_pass = os.environ["MONGO_PASS"]
mongo_host = os.environ["MONGO_HOST"]

client = MongoClient(f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:27017/")
database = client["spotify_metrics"]
collection_play_history = database["play_history"]
collection_artist_genres = database["artist_genres"]
collection_track_energy = database["track_energy"]


def get_last_played_at() -> int:
    """Get the timestamp of the last played song
    
    Returns:
        int: last played timestamp in millisecond epoch
    """
    result = collection_play_history.find().sort("played_at", DESCENDING).limit(1)
    for played in result:
        last_played_at = played["played_at"]
        print(last_played_at, type(last_played_at))
    millisecond_epoch = int(last_played_at.timestamp() * 1000)
    print("Last played:", millisecond_epoch)
    return millisecond_epoch


def upsert_play_history(history: PlayHistoryPaging) -> None:
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
    collection_play_history.bulk_write(requests=requests)


def upsert_artist_genres(artists: List[ArtistGenres]) -> None:
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
    collection_artist_genres.bulk_write(requests)


def upsert_track_energy(tracks: List[TrackEnergy]) -> None:
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
    collection_track_energy.bulk_write(requests)


def refresh_data() -> None:
    """Run the script to scrape data from the spotify API for recently played
        history metrics
    """
    print("Beginning scrape worker")
    from . import scrape

    scrape.refresh_token()

    minutes = 10

    while True:
        last_played = get_last_played_at()
        history = scrape.get_recently_played(scrape.spotify, after=last_played)
        if len(history.items) == 0:
            print(f"Processing history: len={len(history.items)}")
        else:
            print(
                (
                    f"Processing history: len={len(history.items)},",
                    f"after={history.cursors.after},",
                    f"before={history.cursors.before}",
                ),
                flush=True,
            )
            print(len(history.items))
            upsert_play_history(history)

            artist_ids = scrape.extract_artist_ids_from_history(history)
            artists = scrape.get_artists(scrape.spotify, artist_ids)
            artist_genres = scrape.extract_artist_genres(artists)
            upsert_artist_genres(artist_genres)

            track_ids = scrape.extract_track_ids_from_history(history)
            audio_features = scrape.get_audio_features(scrape.spotify, track_ids)
            track_energies = scrape.extract_track_energies(audio_features)
            upsert_track_energy(track_energies)

        print(f"Sleeping for {60*minutes}", flush=True)
        time.sleep(60 * minutes)


if __name__ == "__main__":
    pass
