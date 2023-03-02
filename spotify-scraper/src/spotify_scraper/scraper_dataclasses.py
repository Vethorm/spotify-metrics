from dataclasses import dataclass
from typing import List


@dataclass
class Artist:
    id: str
    name: str

    def __hash__(self):
        return hash(id)


@dataclass
class ArtistGenres:
    id: str
    genres: List[str]


@dataclass
class TrackEnergy:
    id: str
    energy: float


@dataclass
class RecentlyPlayedMetric:
    played_at: int
    track_name: str
    track_id: str
    artists: List[Artist]
    popularity: int
