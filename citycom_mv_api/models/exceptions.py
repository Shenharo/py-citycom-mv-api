class CitycomError(Exception):
    """Exception raised for errors in the citycom API.

    Attributes:
        code -- input salary which caused the error.
        error -- description of the error
    """

    def __init__(self, code, error):
        self.code = code
        self.error = error
        super().__init__(f"(Code {self.code}): {self.error}")


class LoginError(CitycomError):
    """Exception raised for errors in the citycom Login.

    Attributes:
        code -- input salary which caused the error.
        error -- description of the error
    """

    def __init__(self, code, error):
        CitycomError.__init__(self, code, error)


class TwoFactorRequiredError(LoginError):
    """Raised when the password was accepted and a 2FA code was sent.

    Attributes:
        challenge -- the LoginChallenge holding the pending token and where the code was sent
    """

    def __init__(self, challenge):
        self.challenge = challenge
        LoginError.__init__(self, -1, f"2FA code sent via {challenge.channel} to {challenge.masked_contact}")


class TokenExpiredError(LoginError):
    """Raised when the access token expired; a new login with a 2FA code is required."""

    def __init__(self):
        LoginError.__init__(self, -1, "Access token expired, a new login with a 2FA code is required")
