from typing import Optional
from mashumaro import DataClassDictMixin


from dataclasses import dataclass, field


@dataclass
class Location(DataClassDictMixin):
    latitude: Optional[float] = field(default=None, metadata={'alias': 'latitude'})
    longitude: Optional[float] = field(default=None, metadata={'alias': 'longitude'})