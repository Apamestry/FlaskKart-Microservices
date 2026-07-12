import requests
from flask import session, current_app

REQUEST_TIMEOUT = 5  # seconds


class GatewayUnavailable(Exception):
    """The Gateway itself couldn't be reached at all."""
    pass


class SessionExpired(Exception):
    """The Gateway rejected our token (expired/invalid). Session is cleared
    automatically when this is raised - callers just need to redirect."""
    pass


def _headers():
    headers = {"Content-Type": "application/json"}
    token = session.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _check(resp):
    # A 401 only means "your session expired" if we actually sent a token.
    # Without a token (e.g. a login attempt with wrong credentials), a 401
    # is a normal auth failure the caller should handle itself.
    if resp.status_code == 401 and session.get("token"):
        session.clear()
        raise SessionExpired()
    return resp


def _url(path):
    return f"{current_app.config['GATEWAY_URL']}{path}"


def api_get(path, params=None):
    try:
        resp = requests.get(_url(path), headers=_headers(), params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        raise GatewayUnavailable()
    return _check(resp)


def api_post(path, json=None):
    try:
        resp = requests.post(_url(path), headers=_headers(), json=json, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        raise GatewayUnavailable()
    return _check(resp)


def api_patch(path, json=None):
    try:
        resp = requests.patch(_url(path), headers=_headers(), json=json, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        raise GatewayUnavailable()
    return _check(resp)


def api_delete(path):
    try:
        resp = requests.delete(_url(path), headers=_headers(), timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        raise GatewayUnavailable()
    return _check(resp)