# from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import List


class Artist(SQLModel, table=True):
    artist_id: str = Field(primary_key=True)
    artist_name: str
    genres: List[str]
    popularity: int
