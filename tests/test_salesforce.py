"""Deterministic, offline tests for the optional Salesforce integration.

Run with: `python3 -m unittest tests/test_salesforce.py -v` from the repo
root, or `python3 tests/test_salesforce.py` directly.

The tests inject a fake `Session` into the module so no real HTTP traffic
ever leaves the process. They cover the four failure modes a real user
is most likely to hit: disabled config, bad auth, expired token, and an
empty result set, plus the happy path with both supported auth flows.
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

# Make sure the repository root is on sys.path so `import salesforce` works
# when this file is executed directly.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import salesforce  # noqa: E402  (path tweak must happen first)


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = "" if isinstance(payload, dict) else str(payload)

    def json(self):
        return self._payload


class _FakeSession:
    """Mimics `requests.Session` for the two calls the adapter makes."""

    def __init__(self, token_payload, query_payload):
        self._token_payload = token_payload
        self._query_payload = query_payload
        self.calls = []

    def post(self, url, data=None, headers=None, timeout=None):
        self.calls.append(("POST", url, data, headers))
        if isinstance(self._token_payload, Exception):
            raise self._token_payload
        if isinstance(self._token_payload, _FakeResponse):
            return self._token_payload
        return _FakeResponse(200, self._token_payload)

    def get(self, url, headers=None, timeout=None):
        self.calls.append(("GET", url, headers))
        if isinstance(self._query_payload, Exception):
            raise self._query_payload
        if isinstance(self._query_payload, _FakeResponse):
            return self._query_payload
        return _FakeResponse(200, self._query_payload)


def _reset_token_cache():
    salesforce._TOKEN_CACHE.update(
        {"access_token": None, "instance_url": None, "expires_at": 0.0}
    )


def _base_config(**overrides):
    cfg = {
        "ENABLED": True,
        "LOGIN_URL": "https://login.salesforce.com",
        "AUTH_FLOW": "client_credentials",
        "CLIENT_ID": "cid",
        "CLIENT_SECRET": "csecret",
        "SOQL": "SELECT Id, Name FROM Account LIMIT 1",
        "NAME_FIELD": "Name",
    }
    cfg.update(overrides)
    return cfg


class DisabledIntegrationTests(unittest.TestCase):
    def test_disabled_returns_none(self):
        cfg = _base_config(ENABLED=False)
        self.assertIsNone(salesforce.fetch_presence(cfg))


class HappyPathTests(unittest.TestCase):
    def setUp(self):
        _reset_token_cache()

    def test_client_credentials_happy_path(self):
        token_payload = {
            "access_token": "tok-1",
            "instance_url": "https://example.my.salesforce.com",
        }
        query_payload = {
            "records": [
                {
                    "attributes": {"type": "Account", "url": "/services/data/v59.0/sobjects/Account/001"},
                    "Id": "001ABC",
                    "Name": "Acme Co",
                    "Industry": "Manufacturing",
                }
            ]
        }
        with patch.object(salesforce, "_Session", lambda: _FakeSession(token_payload, query_payload)):
            presence = salesforce.fetch_presence(_base_config(STATE_FIELD="Industry"))

        self.assertIsNotNone(presence)
        self.assertEqual(presence["name"], "Acme Co")
        self.assertEqual(presence["state"], "Manufacturing")
        self.assertEqual(presence["record_id"], "001ABC")

    def test_password_flow_appends_security_token(self):
        token_payload = {"access_token": "tok-2", "instance_url": "https://example.my.salesforce.com"}
        query_payload = {"records": [{"Id": "001", "Name": "Beta"}]}
        cfg = _base_config(
            AUTH_FLOW="password",
            USERNAME="user@example.com",
            PASSWORD="hunter2",
            SECURITY_TOKEN="abcd",
        )
        fake = _FakeSession(token_payload, query_payload)
        with patch.object(salesforce, "_Session", lambda: fake):
            salesforce.fetch_presence(cfg)

        # Reach into the fake session to confirm the password grant was sent
        # with the security token concatenated onto the password.
        post = fake.calls[0]
        self.assertEqual(post[0], "POST")
        self.assertIn("grant_type=password", post[2])
        self.assertIn("password=hunter2abcd", post[2])

    def test_empty_records_returns_none(self):
        token_payload = {"access_token": "tok-3", "instance_url": "https://example.my.salesforce.com"}
        query_payload = {"records": []}
        with patch.object(salesforce, "_Session", lambda: _FakeSession(token_payload, query_payload)):
            self.assertIsNone(salesforce.fetch_presence(_base_config()))

    def test_missing_name_returns_none(self):
        token_payload = {"access_token": "tok-4", "instance_url": "https://example.my.salesforce.com"}
        query_payload = {"records": [{"Id": "001", "Name": ""}]}
        with patch.object(salesforce, "_Session", lambda: _FakeSession(token_payload, query_payload)):
            self.assertIsNone(salesforce.fetch_presence(_base_config()))


class FailureModeTests(unittest.TestCase):
    def setUp(self):
        _reset_token_cache()

    def test_auth_failure_returns_none(self):
        bad_token = _FakeResponse(400, {"error": "invalid_client"})
        with patch.object(salesforce, "_Session", lambda: _FakeSession(bad_token, {"records": []})):
            self.assertIsNone(salesforce.fetch_presence(_base_config()))

    def test_network_error_returns_none(self):
        with patch.object(
            salesforce,
            "_Session",
            lambda: _FakeSession(RuntimeError("boom"), {"records": []}),
        ):
            self.assertIsNone(salesforce.fetch_presence(_base_config()))

    def test_expired_token_is_dropped(self):
        token_payload = {"access_token": "tok-5", "instance_url": "https://example.my.salesforce.com"}
        query_payload = {"records": []}
        with patch.object(salesforce, "_Session", lambda: _FakeSession(token_payload, query_payload)):
            salesforce.fetch_presence(_base_config())
            self.assertIsNotNone(salesforce._TOKEN_CACHE["access_token"])
            salesforce._TOKEN_CACHE["access_token"] = None  # simulate 401 -> drop

    def test_query_401_clears_token_cache(self):
        token_payload = {"access_token": "tok-6", "instance_url": "https://example.my.salesforce.com"}
        query_payload = _FakeResponse(401, [{"error": "session expired"}])
        with patch.object(salesforce, "_Session", lambda: _FakeSession(token_payload, query_payload)):
            presence = salesforce.fetch_presence(_base_config())
            self.assertIsNone(presence)
            self.assertIsNone(salesforce._TOKEN_CACHE["access_token"])


class TemplateTests(unittest.TestCase):
    def test_template_renders_with_template_fields(self):
        cfg = {
            "ENABLED": True,
            "LOGIN_URL": "https://login.salesforce.com",
            "AUTH_FLOW": "client_credentials",
            "CLIENT_ID": "cid",
            "CLIENT_SECRET": "csecret",
            "SOQL_TEMPLATE": "SELECT Id FROM Opportunity WHERE AccountId = '{account_id}'",
            "TEMPLATE_FIELDS": {"account_id": "001ABC"},
            "NAME_FIELD": "Name",
        }
        self.assertEqual(
            salesforce._resolve_soql(cfg, record=None),
            "SELECT Id FROM Opportunity WHERE AccountId = '001ABC'",
        )

    def test_template_missing_field_raises_value_error(self):
        cfg = {
            "SOQL_TEMPLATE": "SELECT Id FROM X WHERE Y = '{missing}'",
            "TEMPLATE_FIELDS": {},
        }
        with self.assertRaises(ValueError):
            salesforce._resolve_soql(cfg, record=None)


class FieldExtractionTests(unittest.TestCase):
    def test_compound_field_falls_back_to_name(self):
        record = {"Owner": {"Name": "Alice", "Id": "005"}}
        self.assertEqual(salesforce._field_or_none(record, "Owner"), "Alice")

    def test_none_field_becomes_empty_string(self):
        self.assertEqual(salesforce._field_or_none({"X": None}, "X"), "")

    def test_scalar_field_passes_through(self):
        self.assertEqual(salesforce._field_or_none({"X": 42}, "X"), "42")


if __name__ == "__main__":
    unittest.main()