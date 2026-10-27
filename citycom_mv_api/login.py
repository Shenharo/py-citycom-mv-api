"""Login Module."""

import datetime
import json
from typing import Optional, Union

import aiofiles
import pytz
from aiohttp import ClientSession
from loguru import logger

from citycom_mv_api import commons
from citycom_mv_api.const import LOGIN_URL, SEND_NEW_2FA_URL, VERIFY_2FA_URL
from citycom_mv_api.models.exceptions import LoginError, TwoFactorRequiredError
from citycom_mv_api.models.jwt import JWT
from citycom_mv_api.models.login_challenge import LoginChallenge


def _json_headers(token: Optional[str] = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/plain, */*"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def start_login(
    session: ClientSession, user_name: str, password: str, channel: str = "sms"
) -> Union[JWT, LoginChallenge]:
    """
    Start a login. Citycom now requires 2FA: when the password is accepted, a code is sent via
    `channel` ("sms" or "email") and a LoginChallenge is returned. Pass its pending token and the
    code to verify_2fa_code(). A JWT is returned directly only if the account has no 2FA.
    """
    response = await commons.send_post_request(
        session,
        url=LOGIN_URL,
        headers=_json_headers(),
        json_data={"username": user_name, "password": password, "channel": channel},
    )
    if response.get("pendingToken"):
        return LoginChallenge.from_dict(response)
    if response.get("token"):
        return JWT.from_dict(response["token"])
    raise LoginError(-1, f"Unexpected login response: {list(response)}")


async def verify_2fa_code(session: ClientSession, pending_token: str, code: str) -> JWT:
    """Complete a login with the 2FA code that was sent."""
    response = await commons.send_post_request(
        session, url=VERIFY_2FA_URL, headers=_json_headers(pending_token), json_data={"code": code}
    )
    if not response.get("token"):
        raise LoginError(-1, f"Unexpected 2FA response: {list(response)}")
    return JWT.from_dict(response["token"])


async def send_new_2fa_code(session: ClientSession, pending_token: str, channel: str = "sms") -> Optional[str]:
    """Send a new 2FA code. Returns the masked contact it was sent to."""
    response = await commons.send_post_request(
        session, url=SEND_NEW_2FA_URL, headers=_json_headers(pending_token), json_data={"channel": channel}
    )
    return response.get("sentTo")


async def do_login(session: ClientSession, user_name, password: str) -> Optional[JWT]:
    """
    Login and return a token. Raises TwoFactorRequiredError when a 2FA code was sent
    (which is always the case for Citycom accounts since 2026).
    """
    try:
        result = await start_login(session, user_name, password)
    except LoginError:
        raise
    except Exception as error:
        logger.warning(f"Failed at first login: {error}")
        raise LoginError(-1, "Failed at first login") from error
    if isinstance(result, LoginChallenge):
        raise TwoFactorRequiredError(result)
    return result


async def manual_authorization(session: ClientSession, user_name, password: str) -> Optional[JWT]:  # pragma: no cover
    """Get authorization token from citycom API."""
    if not user_name:
        user_name = await commons.read_user_input("Enter your user: ")
    if not password:
        password = await commons.read_user_input("Enter your password: ")
    try:
        jwt_token = await do_login(session, user_name, password)
    except TwoFactorRequiredError as err:
        code = await commons.read_user_input(f"{err.error}. Enter the code: ")
        jwt_token = await verify_2fa_code(session, err.challenge.pending_token, code)
    logger.debug(
        f"Access token: {jwt_token.access_token}\n"
        f"Refresh token: {jwt_token.refresh_token}\n"
        f"access_token: {jwt_token.access_token}"
    )
    return jwt_token


async def refresh_token(session: ClientSession, token: JWT) -> Optional[JWT]:
    """Refresh JWT token."""
    headers = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded"}
    data = {"refresh_token": token.refresh_token, "grant_type": "refresh_token"}
    commons.add_auth_bearer_to_headers(headers, token.access_token)
    response = await commons.send_post_request(session=session, url=LOGIN_URL, data=data, headers=headers)
    return JWT.from_dict(response)


async def save_token_to_file(token: JWT, path: str = "token.json") -> None:
    """Save token to file."""
    async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(token.to_dict()))


async def load_token_from_file(path: str = "token.json") -> JWT:
    """Load token from file."""
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        contents = await f.read()
    token = json.loads(contents)
    token[".expires"] = token["expires"]

    jwt_data = JWT.from_dict(token)

    return jwt_data


def expires_at(token: JWT) -> Optional[datetime.datetime]:
    """Return when the token expires, or None if unknown."""
    if not token or not token.expires:
        return None
    try:
        # 2FA login: ISO 8601 with offset, e.g. 2026-10-28T03:58:53+02:00
        value = datetime.datetime.fromisoformat(token.expires)
    except ValueError:
        # Old login: RFC 1123, e.g. Tue, 27 Oct 2026 15:58:53 GMT
        value = datetime.datetime.strptime(token.expires, "%a, %d %b %Y %H:%M:%S %Z")
    if value.tzinfo is None:
        value = value.replace(tzinfo=pytz.UTC)
    return value


def is_expired(token: JWT) -> bool:
    value = expires_at(token)
    return value is None or (value - datetime.datetime.now(datetime.UTC)).total_seconds() < 0


def is_about_to_expire(token: JWT) -> bool:
    value = expires_at(token)
    return value is None or (value - datetime.datetime.now(datetime.UTC)).total_seconds() < 300
