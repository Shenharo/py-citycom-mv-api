from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin


@dataclass
class JWT(DataClassDictMixin):
    """JWT Token"""

    access_token: str = None
    refresh_token: str = None
    token_type: str = None
    expires_in: int = None
    expires: str = field(default=None, metadata={"alias": ".expires"})

    @classmethod
    def __pre_deserialize__(cls, d: dict) -> dict:
        # The 2FA login returns "expires" (ISO 8601); the old login returned ".expires".
        if "expires" in d and ".expires" not in d:
            d = {**d, ".expires": d["expires"]}
        return d

    def __eq__(self, other):
        if isinstance(other, JWT):
            return (self.access_token, self.refresh_token, self.token_type, self.expires_in, self.expires) == (
                other.access_token,
                other.refresh_token,
                other.token_type,
                other.expires_in,
                other.expires,
            )
        return False

    def __hash__(self):
        return hash((self.access_token, self.refresh_token, self.token_type, self.expires_in, self.expires))
