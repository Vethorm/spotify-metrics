from spotify_scraper.models.track import PlayedTrack, Track, TrackFeatures
from spotify_scraper.models.artist import Artist
from sqlmodel import SQLModel, create_engine, Session, select, col
from tekore.model import PlayHistoryPaging

from typing import List
import os

class SpotifyMetricsDB:
    def __init__(self, database_uri: str = None):
        if database_uri is None:
            database_uri = os.environ["SPOTIFY_SCRAPER_DATABASE_URI"]
        self.engine = create_engine(database_uri)
        self._create_db_and_tables()

    def _create_db_and_tables(self):
        """lets sqlmodel create our database and tables"""
        SQLModel.metadata.create_all(self.engine)

    def get_last_played_at(self) -> int:
        """Get the timestamp of the last played song

        Returns:
            int: last played timestamp in millisecond epoch
        """
        with Session(self.engine) as session:
            statement = (
                select(PlayedTrack).order_by(col(PlayedTrack.played_at).desc()).limit(1)
            )
            result = session.exec(statement)
            for played in result:
                millisecond_epoch = int(played.played_at.timestamp() * 1000)
                # logger.info(f"Last played: {millisecond_epoch}")
                return millisecond_epoch

    def upsert_play_history(self, history: PlayHistoryPaging) -> None:
        """Upsert the play history to transactional db

        Args:
            history (PlayHistoryPaging): history object of recently played songs
        """
        with Session(self.engine) as session:
            for track in history.items:
                artists = [artist.id for artist in track.track.artists]
                # TODO: check how this handles insert conflicts
                # ideally we are doing upserts
                session.merge(
                    PlayedTrack(
                        played_at=track.played_at,
                        track_id=track.track.id,
                        track_name=track.track.name,
                        artist_ids=artists,
                    )
                )
            session.commit()

    def upsert_track(self, tracks: List[Track]) -> None:
        """upserts a track to the transactional db

        Args:
            tracks (List[Track]): list of tracks to upsert
        """
        with Session(self.engine) as session:
            for track in tracks:
                session.merge(track)
            session.commit()

    def upsert_track_features(self, track_features: List[TrackFeatures]) -> None:
        """upsert track features to the transactional db

        Args:
            track_features (List[TrackFeatures]): list of track features
        """
        with Session(self.engine) as session:
            for track in track_features:
                session.merge(track)
            session.commit()

    def upsert_artist(self, artists: List[Artist]) -> None:
        with Session(self.engine) as session:
            for artist in artists:
                session.merge(artist)
            session.commit()
