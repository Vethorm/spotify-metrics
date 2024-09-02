import logging
from datetime import datetime
from typing import List

from pandas import DataFrame

from sqlmodel import create_engine, Session

from sqlalchemy.sql import text

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
                FROM (
                    SELECT distinct track_id, artist_ids
                    FROM playedtrack 
                    WHERE played_at >= '{after.strftime('%Y-%m-%d')}'
                ) track
                INNER JOIN artist a
                    ON a.artist_id = any(track.artist_ids)
                GROUP BY track.track_id
            )

            SELECT track.played_at, track.track_name, artists.artist_names
            FROM
                (
                    SELECT * 
                    FROM playedtrack 
                    WHERE played_at >= '{after.strftime('%Y-%m-%d')}'
                ) track
                INNER JOIN track_and_artist artists
                ON track.track_id = artists.track_id
            ORDER BY track.played_at DESC
            """
            result = session.exec(text(statement))

            rows = [
                [
                    item[0].strftime("%Y-%m-%d, %H:%M"),
                    item[1],
                    item[2],
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
            result = session.exec(text(statement))

            track_ids = [item[0] for item in result]
        return track_ids

    def read_energy_score(self, after: datetime) -> float:
        """Reads the aggregate energy score from the track list from the
            transactional db

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
            result = session.exec(text(statement))

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
            result = session.exec(text(statement))

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
            FROM
                artist
                INNER JOIN artist_id_counts counts
                    ON artist.artist_id = counts.artist_id
            ORDER BY counts.artist_play_count DESC
            LIMIT 5
            """  # noqa: E501
            result = session.exec(text(statement))

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
            LIMIT 5
            """  # noqa: E501
            result = session.exec(text(statement))

            rows = [item[0] for item in result]
        df = DataFrame(rows, columns=["Genre"])
        return df

    def read_listen_time_aggregation(self, start: datetime, end: datetime) -> DataFrame:
        """Reads the total listen duration by date

        Args:
            start (datetime): inclusive start date to calculate
            end (datetime): inclusive end date to calculate

        Returns:
            DataFrame: dataframe of 'date' and 'listen_time'
        """
        with Session(self.engine) as session:
            statement = f"""
            SELECT 
                CAST(track.played_at AS DATE) as played_at,
                SUM(feat.duration_ms) as total_duration
            FROM (
                    SELECT *
                    FROM playedtrack
                    WHERE CAST(played_at AS DATE) >= '{start.strftime('%Y-%m-%d')}'
                        AND CAST(played_at AS DATE) <= '{end.strftime('%Y-%m-%d')}' 
                ) track
                INNER JOIN trackfeatures feat
                ON track.track_id = feat.track_id
            GROUP BY CAST(track.played_at AS DATE)
            """  # noqa: E501
            result = session.exec(text(statement))

            rows = [
                (item[0].strftime("%m/%d"), round(item[1] / (1000 * 60)))
                for item in result
            ]
        pd = DataFrame(rows, columns=["date", "listen_time"])
        return pd

    def read_popularity_aggregation(self, start: datetime, end: datetime) -> DataFrame:
        """_summary_

        Args:
            start (datetime): _description_
            end (datetime): _description_

        Returns:
            DataFrame: _description_
        """
        with Session(self.engine) as session:
            statement = f"""
            SELECT
                CAST(played.played_at AS DATE) as played_at,
                ROUND(AVG(track.popularity), 0) as avg_popularity
            FROM (
                    SELECT *
                    FROM playedtrack
                    WHERE CAST(played_at AS DATE) >= '{start.strftime('%Y-%m-%d')}'
                            AND CAST(played_at AS DATE) <= '{end.strftime('%Y-%m-%d')}'
                ) played
                INNER JOIN track
                ON played.track_id = track.track_id
            GROUP BY CAST(played.played_at AS DATE)
            """
            result = session.exec(text(statement))

            rows = [(item[0].strftime("%m/%d"), item[1]) for item in result]
        df = DataFrame(rows, columns=["date", "popularity"])
        return df

    def read_energy_aggregation(self, start: datetime, end: datetime) -> DataFrame:
        """_summary_

        Args:
            start (datetime): _description_
            end (datetime): _description_

        Returns:
            DataFrame: _description_
        """
        with Session(self.engine) as session:
            statement = f"""
            SELECT 
                CAST(track.played_at AS DATE) as played_at,
                ROUND(AVG(feat.energy::numeric) * 100, 0) as avg_energy
            FROM (
                    SELECT *
                    FROM playedtrack
                    WHERE CAST(played_at AS DATE) >= '{start.strftime('%Y-%m-%d')}'
                        AND CAST(played_at AS DATE) <= '{end.strftime('%Y-%m-%d')}' 
                ) track
                INNER JOIN trackfeatures feat
                ON track.track_id = feat.track_id
            GROUP BY CAST(track.played_at AS DATE)
            """
            result = session.exec(text(statement))

            rows = [(item[0].strftime("%m/%d"), item[1]) for item in result]
        df = DataFrame(rows, columns=["date", "energy"])
        return df

    def read_danceability_aggregation(
        self, start: datetime, end: datetime
    ) -> DataFrame:
        """_summary_

        Args:
            start (datetime): _description_
            end (datetime): _description_

        Returns:
            DataFrame: _description_
        """
        with Session(self.engine) as session:
            statement = f"""
            SELECT 
                CAST(track.played_at AS DATE) as played_at,
                ROUND(AVG(feat.danceability::numeric) * 100, 0) as avg_energy
            FROM (
                    SELECT *
                    FROM playedtrack
                    WHERE CAST(played_at AS DATE) >= '{start.strftime('%Y-%m-%d')}'
                        AND CAST(played_at AS DATE) <= '{end.strftime('%Y-%m-%d')}' 
                ) track
                INNER JOIN trackfeatures feat
                ON track.track_id = feat.track_id
            GROUP BY CAST(track.played_at AS DATE)
            """
            result = session.exec(text(statement))

            rows = [(item[0].strftime("%m/%d"), item[1]) for item in result]
        df = DataFrame(rows, columns=["date", "danceability"])
        return df
