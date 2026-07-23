# Optional Salesforce -> Discord rich-presence bridge for steam-presence.
#
# Disabled by default. Pure stdlib so the script's existing `requirements.txt`
# does not have to change. When `SALESFORCE.ENABLED` is true the presence
# updater will, every cycle, run a SOQL query against a configured Salesforce
# instance and map the first record's selected fields into the existing
# Discord presence model (game name, rich presence state, optional icon).
#
# Authentication flows supported out of the box (both are gated by config):
#   - `client_credentials` (OAuth 2.0 client credentials grant) — for
#     server-to-server integrations, requires a Connected App with the
#     "Run As" user pre-authorised.
#   - `password`           (OAuth 2.0 username-password grant) — for
#     sandboxes and trusted local integrations, requires the Connected App
#     to allow the "Allow OAuth Username-Password Flows" policy.
#
# A security token is always appended to the password when using the
# username-password flow (the Salesforce API requires it).
#
# This module does not log secrets and does not echo config values back.

from datetime import datetime
from json import dumps as _json_dumps
from time import time as _time
from urllib.parse import urlencode

try:
    # only used inside the adapter, kept lazy so the script still imports
    # cleanly on systems without requests (the parent script falls back to
    # its own installer flow in that case).
    from requests import Session as _Session
except Exception:  # pragma: no cover - parent script handles install prompt
    _Session = None


_LOG_PREFIX = "[salesforce]"
_TOKEN_CACHE = {"access_token": None, "instance_url": None, "expires_at": 0.0}


def _log(msg):
    print(f"[{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {_LOG_PREFIX} {msg}")


def _error(msg):
    print(
        f"    ERROR: [{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {_LOG_PREFIX} {msg}"
    )


def _require_session():
    if _Session is None:
        raise RuntimeError(
            "the `requests` package is required for the Salesforce integration. "
            "Run `pip install -r requirements.txt` and try again."
        )
    return _Session()


def _auth_payload(config):
    """Build the OAuth 2.0 token-request payload for the configured flow."""
    flow = (config.get("AUTH_FLOW") or "client_credentials").lower()
    if flow == "client_credentials":
        return {
            "grant_type": "client_credentials",
            "client_id": config["CLIENT_ID"],
            "client_secret": config["CLIENT_SECRET"],
        }

    if flow == "password":
        username = config["USERNAME"]
        password = config["PASSWORD"]
        # Salesforce's username-password flow requires the security token
        # concatenated onto the password when the trust IP range is off
        # (which is the default for sandboxes and Developer orgs).
        token = config.get("SECURITY_TOKEN") or ""
        if token and not password.endswith(token):
            password = f"{password}{token}"

        return {
            "grant_type": "password",
            "client_id": config["CLIENT_ID"],
            "client_secret": config["CLIENT_SECRET"],
            "username": username,
            "password": password,
        }

    raise ValueError(
        f"unsupported AUTH_FLOW `{flow}`; expected `client_credentials` or `password`"
    )


def _login_url(login_url):
    # The OAuth 2.0 token endpoint is the same path on production, sandbox,
    # and custom domains. The caller passes the org base URL in `LOGIN_URL`.
    return f"{login_url.rstrip('/')}/services/oauth2/token"


def _request_token(config, force=False):
    """Return a cached `(access_token, instance_url)` pair.

    Tokens are reused until 60 seconds before their declared expiry. Callers
    can pass `force=True` to bypass the cache (used by the tests).
    """
    cached = _TOKEN_CACHE
    now = _time()
    if not force and cached["access_token"] and cached["expires_at"] > now:
        return cached["access_token"], cached["instance_url"]

    if not config.get("LOGIN_URL"):
        raise ValueError("SALESFORCE.LOGIN_URL is required")

    session = _require_session()
    payload = _auth_payload(config)
    resp = session.post(
        _login_url(config["LOGIN_URL"]),
        data=_urlencode(payload),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Salesforce auth failed: HTTP {resp.status_code} {resp.text[:200]}"
        )

    body = resp.json()
    access_token = body.get("access_token")
    instance_url = body.get("instance_url")
    if not access_token or not instance_url:
        raise RuntimeError(
            "Salesforce auth response missing access_token or instance_url"
        )

    # The OAuth 2.0 token endpoint does not return an explicit expiry for the
    # grants we support; assume the default 2h session lifetime and refresh
    # before that.
    cached["access_token"] = access_token
    cached["instance_url"] = instance_url
    cached["expires_at"] = now + 2 * 3600 - 60
    return access_token, instance_url


def _urlencode(payload):
    """`urllib.parse.urlencode` wrapper kept local for easy test patching."""
    return urlencode(payload)


def _run_soql(config, access_token, instance_url, soql):
    session = _require_session()
    encoded = _urlencode({"q": soql})
    url = f"{instance_url.rstrip('/')}/services/data/v59.0/query?{encoded}"
    resp = session.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if resp.status_code == 401:
        # Token rejected -> drop cache so the next cycle re-auths.
        _TOKEN_CACHE["access_token"] = None
        raise RuntimeError("Salesforce session expired (HTTP 401)")
    if resp.status_code != 200:
        raise RuntimeError(
            f"Salesforce query failed: HTTP {resp.status_code} {resp.text[:200]}"
        )
    body = resp.json()
    return body.get("records", [])


def _resolve_soql(config, record):
    """Allow the user to use either a literal SOQL string or a small template
    with `{field}` placeholders that are filled in from the configured
    `TEMPLATE_FIELDS` dict. The literal path is the default and the simplest
    to reason about.
    """
    soql = config.get("SOQL")
    if soql:
        return soql

    template = config.get("SOQL_TEMPLATE")
    fields = config.get("TEMPLATE_FIELDS") or {}
    if not template:
        raise ValueError(
            "SALESFORCE.SOQL or SALESFORCE.SOQL_TEMPLATE must be configured"
        )
    try:
        return template.format(**fields)
    except KeyError as missing:
        raise ValueError(
            f"SALESFORCE.SOQL_TEMPLATE references unknown field {missing.args[0]!r}"
        ) from None


def _field_or_none(record, key):
    """Salesforce returns `None` for unset fields and nested attributes
    surface as dicts; both should render as an empty string in the presence."""
    value = record.get(key)
    if value is None:
        return ""
    if isinstance(value, dict):
        # Compound fields (e.g. Account.Owner.Name) are returned as nested
        # dicts; fall back to a common "Name" attribute when present.
        return value.get("Name") or value.get("Title") or ""
    return str(value)


def fetch_presence(config):
    """Return a dict describing the Discord rich presence to push.

    `None` is returned when the integration is disabled, when no records
    match the SOQL query, or when an upstream error should be treated as
    "no presence this cycle" by the caller. Errors are logged so the main
    loop does not have to special-case them.
    """
    if not config or not config.get("ENABLED"):
        return None

    try:
        access_token, instance_url = _request_token(config)
        soql = _resolve_soql(config, record=None)
        records = _run_soql(config, access_token, instance_url, soql)
    except Exception as exc:
        _error(f"failed to fetch Salesforce presence: {exc}")
        return None

    if not records:
        return None

    record = records[0]
    name_field = config.get("NAME_FIELD", "Name")
    state_field = config.get("STATE_FIELD")
    details_field = config.get("DETAILS_FIELD")

    name = _field_or_none(record, name_field)
    if not name:
        return None

    presence = {
        "name": name,
        "record_id": record.get("Id") or record.get("attributes", {}).get("url", ""),
        "fields": {k: _field_or_none(record, k) for k in record.keys() if k != "attributes"},
    }

    if state_field:
        presence["state"] = _field_or_none(record, state_field)
    if details_field:
        presence["details"] = _field_or_none(record, details_field)

    icon_url = config.get("ICON_URL")
    if icon_url:
        presence["icon_url"] = icon_url
        presence["icon_text"] = config.get("ICON_TEXT", "Salesforce")

    _log(f"resolved Salesforce presence for `{name}`")
    return presence


def _selftest_payload():  # pragma: no cover - helper for manual smoke tests
    """A minimal payload used by the bundled tests; never enabled by default."""
    return {
        "ENABLED": True,
        "LOGIN_URL": "https://login.salesforce.com",
        "AUTH_FLOW": "client_credentials",
        "CLIENT_ID": "test",
        "CLIENT_SECRET": "test",
        "SOQL": "SELECT Id, Name FROM Account LIMIT 1",
        "NAME_FIELD": "Name",
        "STATE_FIELD": "Industry",
    }


if __name__ == "__main__":  # pragma: no cover - manual smoke entry
    # Lets the user run `python3 salesforce.py` to confirm config + auth
    # without needing the rest of the script.
    print(_json_dumps(fetch_presence(_selftest_payload()), indent=2, default=str))