from pymongo import MongoClient, DESCENDING
from pandas import DataFrame
from datetime import datetime
from typing import List

import os

mongo_user = os.environ["MONGO_USER"]
mongo_pass = os.environ["MONGO_PASS"]
mongo_host = os.environ["MONGO_HOST"]

client = MongoClient(f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:27017/")
database = client["spotify_metrics"]
collection_play_history = database["play_history"]
collection_artist_genres = database["artist_genres"]
collection_track_energy = database["track_energy"]


def read_recently_played(after: datetime) -> DataFrame:
    """Reads the recently played songs from mongodb
    Args:
        after (datetime): datetime in UTC to find the lower bound of dates to
            check
    
    Returns:
        DataFrame
    """
    print("Reading recently played since", after)
    result = collection_play_history.find(filter={"played_at": {"$gte": after}}).sort(
        [("played_at", DESCENDING)]
    )
    rows = [
        [
            item["played_at"].strftime("%Y-%m-%d, %H:%M"),
            item["track_name"],
            ", ".join([artist["name"] for artist in item["artists"]]),
        ]
        for item in result
    ]
    df = DataFrame(rows, columns=["Time played", "Track", "Artist(s)"])
    return df


def read_track_ids(after: datetime) -> List[str]:
    """Reads the track ids for recently played songs from mongodb
    Args:
        after (datetime): datetime in UTC to find the lower bound of dates to
            check
    
    Returns:
        DataFrame
    """
    print("Reading track ids after", after)
    result = collection_play_history.find(filter={"played_at": {"$gte": after}})
    track_ids = [item["track_id"] for item in result]
    return track_ids


def read_energy_score(track_ids: List[str]) -> float:
    """Reads the aggregate energy score from the track list from mongodb

    Args:
        track_ids (List[str]): track ids to aggregate

    Returns:
        float: aggregate energy score
    """
    result = collection_track_energy.aggregate(
        pipeline=[
            {"$match": {"id": {"$in": track_ids}}},
            {"$group": {"_id": None, "energy_score": {"$avg": "$energy"}}},
        ]
    )
    for item in result:
        energy_score = item["energy_score"] * 100
    return energy_score


def read_popularity(track_ids: List[str]) -> float:
    """Reads the aggregate popularity score from the track list from mongodb

    Args:
        track_ids (List[str]): track ids to aggregate

    Returns:
        float: aggregate popularity score
    """
    print(f"Aggregating popularity with {len(track_ids)} track ids!")
    result = collection_play_history.aggregate(
        pipeline=[
            {"$match": {"track_id": {"$in": track_ids}}},
            {"$group": {"_id": None, "popularity_score": {"$avg": "$popularity"}}},
        ]
    )
    popularity_score = 100
    for item in result:
        popularity_score = item["popularity_score"]
    return popularity_score


def read_top_artists(track_ids: List[str]) -> DataFrame:
    """Reads the aggregate top artists from the track list from mongodb

    Args:
        track_ids (List[str]): track ids to aggregate

    Return:
        DataFrame
    """
    result = collection_play_history.aggregate(
        pipeline=[
            {"$match": {"track_id": {"$in": track_ids}}},
            {"$project": {"artists": 1}},
            {"$unwind": {"path": "$artists"}},
            {"$group": {"_id": "$artists.name", "artist_count": {"$count": {}}}},
            {"$sort": {"artist_count": -1, "_id": 1}},
            {"$limit": 5},
        ]
    )
    rows = [item["_id"] for item in result]
    df = DataFrame(rows, columns=["Artist"])
    return df


def read_top_genres(track_ids: List[str]) -> DataFrame:
    """Reads the aggregate top genres from the track list from mongodb
    
    Args:
        track_ids (List[str]): track ids to aggregate

    Return:
        DataFrame"""
    result = collection_play_history.find(filter={"track_id": {"$in": track_ids}})
    artist_ids = [artist["id"] for item in result for artist in item["artists"]]
    result = collection_artist_genres.aggregate(
        pipeline=[
            {"$match": {"id": {"$in": artist_ids}}},
            {"$unwind": {"path": "$genres"}},
            {"$group": {"_id": "$genres", "genre_count": {"$count": {}}}},
            {"$sort": {"genre_count": -1, "_id": 1}},
            {"$limit": 5},
        ]
    )
    rows = [item["_id"] for item in result]
    df = DataFrame(rows, columns=["Genre"])
    return df
