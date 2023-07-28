# from pydantic import BaseModel
from sqlmodel import SQLModel, Field, ARRAY, Column, String
from typing import List


class Artist(SQLModel, table=True):
    artist_id: str = Field(primary_key=True)
    artist_name: str
    genres: List[str] = Field(sa_column=Column(ARRAY(String)))
    popularity: int
