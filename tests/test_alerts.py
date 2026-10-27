"""Tests for active alerts and meter lookup (no network)."""

import asyncio
import datetime

from citycom_mv_api import data
from citycom_mv_api.citycom_mv_client import CityComMVClient
from citycom_mv_api.models.Alert import parse_alerts
from citycom_mv_api.models.jwt import JWT

FUTURE = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=10)).isoformat()
ALERT = {"alertId": 5, "meterId": 111, "alertTypeId": 2, "alertTypeName": "Leak", "extra": "x"}
WEB_ALERT = {"alertTypeId": 7, "date": "2026-10-27T08:30:00"}


class FakeResponse:
    status = 200
    reason = "OK"

    def __init__(self, body):
        self._body = body

    async def json(self, content_type=None):
        return self._body


class FakeSession:
    def __init__(self, body):
        self.body = body
        self.urls = []

    async def get(self, url, headers=None, timeout=None):
        self.urls.append(url)
        return FakeResponse(self.body)


def test_parse_alerts_list_and_wrapped_and_empty():
    alerts = parse_alerts([ALERT])
    assert alerts[0].alert_type == "Leak"
    assert alerts[0].raw["extra"] == "x"
    assert parse_alerts({"alerts": [ALERT]})[0].alert_id == 5
    assert parse_alerts([]) == []
    assert parse_alerts(None) == []


def test_client_get_active_alerts():
    session = FakeSession([ALERT])
    client = CityComMVClient("user", "pass", session)
    client._token = JWT(access_token="a", expires=FUTURE)

    alerts = asyncio.run(client.get_active_alerts("111"))

    assert session.urls[0].endswith("/alerts/active/111")
    assert [a.meter_id for a in alerts] == [111]


def test_get_meter_by_id_matches_meter_id():
    customer = {"properties": [{"meters": [{"meterId": 111}, {"meterId": 222}]}]}
    session = FakeSession(customer)
    token = JWT(access_token="a", expires=FUTURE)

    assert asyncio.run(data.get_meter_by_id(session, token, "222")).meter_id == 222
    assert asyncio.run(data.get_meter_by_id(session, token, "999")) is None


def test_alert_as_returned_by_the_web_app_has_type_and_date():
    alert = parse_alerts([WEB_ALERT])[0]
    assert alert.alert_type_id == 7
    assert alert.date == datetime.datetime(2026, 10, 27, 8, 30)


def test_client_get_alert_types():
    session = FakeSession([{"alertTypeId": 7, "title": "Leak", "meterType": 2, "other": 1}])
    client = CityComMVClient("user", "pass", session)
    client._token = JWT(access_token="a", expires=FUTURE)

    types = asyncio.run(client.get_alert_types())

    assert session.urls[0].endswith("/lookups/alertTypes")
    assert [(t.alert_type_id, t.title) for t in types] == [(7, "Leak")]
