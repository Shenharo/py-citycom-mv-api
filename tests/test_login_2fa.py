"""Tests for the 2FA login flow (no network)."""

import asyncio
import datetime

import pytest

from citycom_mv_api import login
from citycom_mv_api.citycom_mv_client import CityComMVClient
from citycom_mv_api.const import LOGIN_URL, SEND_NEW_2FA_URL, VERIFY_2FA_URL
from citycom_mv_api.models.exceptions import CitycomError, TokenExpiredError, TwoFactorRequiredError
from citycom_mv_api.models.jwt import JWT
from citycom_mv_api.models.login_challenge import LoginChallenge

FUTURE = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=10)).isoformat()
PAST = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1)).isoformat()

PENDING = {
    "pendingToken": "pending",
    "channel": "email",
    "maskedContact": "s***@gmail.com",
    "hasPhone": True,
    "hasEmail": True,
}
VERIFIED = {"token": {"access_token": "access", "expires": FUTURE}, "slowDownSite": False, "canEnterWebSite": True}


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self.reason = "Bad Request" if status != 200 else "OK"
        self._body = body

    async def json(self, content_type=None):
        return self._body


class FakeSession:
    """Records POSTs and answers from a {url: (status, body)} table."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def post(self, url, data=None, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return FakeResponse(*self.responses[url])


def run(coro):
    return asyncio.run(coro)


def test_start_login_returns_challenge():
    session = FakeSession({LOGIN_URL: (200, PENDING)})
    result = run(login.start_login(session, "user", "pass", "email"))

    assert isinstance(result, LoginChallenge)
    assert result.pending_token == "pending"
    assert result.masked_contact == "s***@gmail.com"
    assert session.calls[0]["json"] == {"username": "user", "password": "pass", "channel": "email"}


def test_verify_sends_pending_token_and_parses_iso_expiry():
    session = FakeSession({VERIFY_2FA_URL: (200, VERIFIED)})
    token = run(login.verify_2fa_code(session, "pending", "123456"))

    assert session.calls[0]["headers"]["Authorization"] == "Bearer pending"
    assert session.calls[0]["json"] == {"code": "123456"}
    assert token.access_token == "access"
    assert not login.is_expired(token)


def test_old_expiry_format_still_parses():
    token = JWT.from_dict({"access_token": "a", ".expires": "Tue, 27 Oct 2020 15:58:53 GMT"})
    assert login.is_expired(token)


def test_wrong_code_raises():
    session = FakeSession({VERIFY_2FA_URL: (400, {"error_description": "Invalid code"})})
    with pytest.raises(CitycomError) as err:
        run(login.verify_2fa_code(session, "pending", "000000"))
    assert err.value.code == 400


def test_do_login_raises_two_factor_required():
    session = FakeSession({LOGIN_URL: (200, PENDING)})
    with pytest.raises(TwoFactorRequiredError) as err:
        run(login.do_login(session, "user", "pass"))
    assert err.value.challenge.pending_token == "pending"


def test_client_full_flow():
    session = FakeSession(
        {LOGIN_URL: (200, PENDING), VERIFY_2FA_URL: (200, VERIFIED), SEND_NEW_2FA_URL: (200, {"sentTo": "x"})}
    )
    client = CityComMVClient("user", "pass", session)

    challenge = run(client.login(channel="email"))
    assert challenge.channel == "email"
    assert run(client.send_new_2fa_code("email")) == "x"
    run(client.verify_2fa_code("123456"))

    assert client.logged_in
    assert client.token_expires_at > datetime.datetime.now(datetime.UTC)
    assert run(client.check_token())


def test_client_expired_token_raises():
    client = CityComMVClient("user", "pass", FakeSession({}))
    run(client.load_jwt_token(JWT(access_token="a", expires=FUTURE)))
    client._token = JWT(access_token="a", expires=PAST)

    with pytest.raises(TokenExpiredError):
        run(client.check_token())
    assert not client.logged_in
