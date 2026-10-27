from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from mashumaro import DataClassDictMixin


@dataclass
class Alert(DataClassDictMixin):
    """An active alert of a meter (leak, abnormal flow, no reading...).

    The server schema is not documented; unknown fields are kept in `raw`.
    """

    alert_id: Optional[int] = field(default=None, metadata={"alias": "alertId"})
    meter_id: Optional[int] = field(default=None, metadata={"alias": "meterId"})
    alert_type_id: Optional[int] = field(default=None, metadata={"alias": "alertTypeId"})
    alert_type: Optional[str] = field(default=None, metadata={"alias": "alertTypeName"})
    status_id: Optional[int] = field(default=None, metadata={"alias": "alertStatusId"})
    description: Optional[str] = field(default=None, metadata={"alias": "description"})
    start_date: Optional[datetime] = field(default=None, metadata={"alias": "startDate"})
    raw: dict[str, Any] = field(default_factory=dict, metadata={"alias": "_raw"})

    @classmethod
    def parse(cls, item: dict[str, Any]) -> "Alert":
        """Build an Alert from a server item, keeping the original payload."""
        return cls.from_dict({**item, "_raw": item})


def parse_alerts(response: Any) -> list[Alert]:
    """Accept a bare list, or a dict wrapping the list, and return Alerts."""
    if isinstance(response, dict):
        response = next((v for v in response.values() if isinstance(v, list)), [])
    return [Alert.parse(item) for item in response or [] if isinstance(item, dict)]
