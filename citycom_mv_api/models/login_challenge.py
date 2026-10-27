from dataclasses import dataclass, field
from typing import Optional

from mashumaro import DataClassDictMixin


@dataclass
class LoginChallenge(DataClassDictMixin):
    """Returned by the login endpoint when a 2FA code was sent."""

    pending_token: str = field(metadata={"alias": "pendingToken"})
    channel: Optional[str] = field(default=None, metadata={"alias": "channel"})
    masked_contact: Optional[str] = field(default=None, metadata={"alias": "maskedContact"})
    has_phone: Optional[bool] = field(default=None, metadata={"alias": "hasPhone"})
    has_email: Optional[bool] = field(default=None, metadata={"alias": "hasEmail"})
