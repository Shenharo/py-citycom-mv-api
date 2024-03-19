from citycom_mv_api.models.Reading import MeterReadings


from mashumaro import DataClassDictMixin


from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MetersInfo(DataClassDictMixin):
    water_summery: Optional[MeterReadings] = field(default=None, metadata={'alias': 'waterSummery'})
    alerts: Optional[Any] = field(default=None, metadata={'alias': 'alerts'})