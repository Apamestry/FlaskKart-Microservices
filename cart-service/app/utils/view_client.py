import requests
from flask import current_app

REQUEST_TIMEOUT = 5  # seconds


class ViewServiceUnavailable(Exception):
    """Raised when View Service can't be reached at all (down, timeout, network error)."""
    pass


def fetch_product(product_id):
    """Returns the product dict from View Service, or None if it doesn't exist.

    Raises ViewServiceUnavailable if View Service itself can't be reached —
    callers should turn that into a 503, not a 500 or a silent failure.
    """
    url = f"{current_app.config['VIEW_SERVICE_URL']}/products/{product_id}"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        raise ViewServiceUnavailable()

    if resp.status_code == 404:
        return None

    resp.raise_for_status()
    return resp.json()