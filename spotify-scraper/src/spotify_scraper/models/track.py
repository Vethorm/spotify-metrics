# from pydantic import BaseModel
from sqlmodel import SQLModel, Field, ARRAY, Column, String
from typing import List
from datetime import datetime


class PlayedTrack(SQLModel, table=True):
    played_at: datetime = Field(default_factory=datetime.utcnow, primary_key=True)
    track_id: str = Field(index=True)
    track_name: str
    artist_ids: List[str] = Field(sa_column=Column(ARRAY(String)))


class Track(SQLModel, table=True):
    track_id: str = Field(primary_key=True)
    artist_ids: List[str] = Field(sa_column=Column(ARRAY(String)))
    popularity: int


class TrackFeatures(SQLModel, table=True):
    track_id: str = Field(primary_key=True)
    acousticness: float
    danceability: float
    duration_ms: int
    energy: float
    instrumentalness: float
    key: int
    liveness: float
    loudness: float
    mode: int
    speechiness: float
    tempo: float
    time_signature: int
    type: str
    valence: float
