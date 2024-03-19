from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin


@dataclass
class JWT(DataClassDictMixin):
    """JWT Token"""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    expires: str = field(default=None, metadata={"alias": ".expires"})

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
