from dataclasses import dataclass, field
from typing import Optional

from mashumaro import DataClassDictMixin


@dataclass
class AlertType(DataClassDictMixin):
    """An entry of the alert types lookup, giving a readable title to Alert.alert_type_id."""

    alert_type_id: Optional[int] = field(default=None, metadata={"alias": "alertTypeId"})
    title: Optional[str] = field(default=None, metadata={"alias": "title"})
    meter_type: Optional[int] = field(default=None, metadata={"alias": "meterType"})
