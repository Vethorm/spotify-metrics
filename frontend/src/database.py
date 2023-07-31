import logging
from datetime import datetime
from typing import List

from pandas import DataFrame

from sqlmodel import create_engine, col, Session, select, func as F

from .models.track import PlayedTrack
from .models.artist import Artist

from collections import namedtuple

import os

logger = logging.getLogger("dash.dash")


class SpotifyMetricsDB:
    def __init__(self, database_uri: str = None):
        if database_uri is None:
            database_uri = os.environ["SPOTIFY_SCRAPER_DATABASE_URI"]
        self.engine = create_engine(database_uri)

    def read_recently_played(self, after: datetime) -> DataFrame:
        """Reads the recently played songs from the transactional db

        Args:
            after (datetime): datetime in UTC to find the lower bound of dates to
                check

        Returns:
            DataFrame
        """
        with Session(self.engine) as session:
            statement = f"""
            WITH track_and_artist AS (
                SELECT track.track_id, STRING_AGG(a.artist_name, ', ') as artist_names
                FROM (SELECT * FROM playedtrack WHERE played_at >= '{after.strftime('%Y-%m-%d')}') track
                INNER JOIN artist a
                    ON a.artist_id = any(track.artist_ids)
                GROUP BY track.track_id
            )

            SELECT track.played_at, track.track_id, artists.artist_names
            FROM
                (SELECT * FROM playedtrack WHERE played_at >= '{after.strftime('%Y-%m-%d')}') track
                INNER JOIN track_and_artist artists
                ON track.track_id = artists.track_id
            ORDER BY track.played_at DESC
            """
            result = session.exec(statement)

            rows = [
                [
                    item[0].strftime("%Y-%m-%d, %H:%M"),
                    item[1],
                    ", ".join([artist["name"] for artist in item[2]]),
                ]
                for item in result
            ]
        df = DataFrame(rows, columns=["Time played", "Track", "Artist(s)"])
        return df


    def read_track_ids(self, after: datetime) -> List[str]:
        """Reads the track ids for recently played songs from the transactional db

        Args:
            after (datetime): datetime in UTC to find the lower bound of dates to
                check

        Returns:
            List[str]
        """
        with Session(self.engine) as session:
            statement = f"""
            SELECT track_id
            FROM playedtrack
            WHERE played_at >= '{after.strftime('%Y-%m-%d')}'
            """
            result = session.exec(statement)

            track_ids = [item[0] for item in result]
        return track_ids


    def read_energy_score(self, after: datetime) -> float:
        """Reads the aggregate energy score from the track list from the transactional db

        Args:
            after (datetime): datetime in UTC to find the lower bound of dates to
                check

        Returns:
            float: aggregate energy score
        """
        with Session(self.engine) as session:
            statement = f"""
            WITH track_ids AS (
                SELECT track_id
                FROM playedtrack
                WHERE played_at >= '{after.strftime('%Y-%m-%d')}'
            )

            SELECT AVG(feat.energy)
            FROM track_ids ids
                INNER JOIN trackfeatures feat
                ON ids.track_id = feat.track_id
            """
            result = session.exec(statement)

            for item in result:
                energy_score = item[0] * 100
        return energy_score

    def read_popularity(self, after: datetime) -> float:
        """Reads the aggregate popularity score from the track list from mongodb

        Args:
            after (datetime): datetime in UTC to find the lower bound of dates to
                check

        Returns:
            float: aggregate popularity score
        """
        with Session(self.engine) as session:
            statement = f"""
            WITH track_ids AS (
                SELECT track_id
                FROM playedtrack
                WHERE played_at >= '{after.strftime('%Y-%m-%d')}'
            )

            SELECT AVG(tracks.popularity)
            FROM track_ids ids
                INNER JOIN track tracks
                ON ids.track_id = tracks.track_id
            """
            result = session.exec(statement)

            for item in result:
                popularity_score = item[0]
        return popularity_score

    def read_top_artists(self, after: datetime) -> DataFrame:
        """Reads the aggregate top artists from the track list from mongodb

        Args:
            after (datetime): datetime in UTC to find the lower bound of dates to
                check

        Return:
            DataFrame
        """
        with Session(self.engine) as session:
            statement = f"""
            WITH artist_id_counts AS (
                SELECT a.artist_id, COUNT(*) as artist_play_count
                FROM (SELECT * FROM playedtrack WHERE played_at >= '{after.strftime('%Y-%m-%d')}') track
                INNER JOIN artist a
                    ON a.artist_id = any(track.artist_ids)
                GROUP BY a.artist_id
            )

            SELECT artist.artist_name
            FROM artist
                INNER JOIN artist_id_counts
                ON artist.artist_id = artist_id_counts
            ORDER BY counts.artist_play_count DESC
            """
            result = session.exec(statement)

            rows = [item[0] for item in result]
        df = DataFrame(rows, columns=["Artist"])
        return df

    def read_top_genres(self, after: datetime) -> DataFrame:
        """Reads the aggregate top genres from the track list from mongodb

        Args:
            after (datetime): datetime in UTC to find the lower bound of dates to
                check

        Return:
            DataFrame
        """
        with Session(self.engine) as session:
            statement = f"""
            WITH track_and_artist AS (
                SELECT track.track_id, unnest(a.genres) as genre
                FROM (SELECT * FROM playedtrack WHERE played_at >= '{after.strftime('%Y-%m-%d')}') track
                INNER JOIN artist a
                    ON a.artist_id = any(track.artist_ids)
            ), track_and_distinct_genre AS (
                SELECT DISTINCT track_id, genre
                FROM track_and_artist
                ORDER BY track_id
            )

            SELECT genre, COUNT(*) as genre_play_count
            FROM track_and_distinct_genre
            GROUP BY genre
            ORDER BY COUNT(*) DESC
            """
            result = session.exec(statement)

            rows = [item[0] for item in result]
        df = DataFrame(rows, columns=["Genre"])
        return df
