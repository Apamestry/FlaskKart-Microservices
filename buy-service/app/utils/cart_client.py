import requests
from flask import current_app

REQUEST_TIMEOUT = 5


class CartServiceUnavailable(Exception):
    pass


def get_cart(auth_header):
    """Fetches the current user's cart. auth_header is the original
    'Bearer <token>' string forwarded from the incoming request, since
    Cart Service verifies it independently rather than trusting Buy Service."""
    url = f"{current_app.config['CART_SERVICE_URL']}/cart"
    try:
        resp = requests.get(url, headers={"Authorization": auth_header}, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        raise CartServiceUnavailable()

    resp.raise_for_status()
    return resp.json()


def clear_cart(auth_header):
    url = f"{current_app.config['CART_SERVICE_URL']}/cart/clear"
    try:
        resp = requests.delete(url, headers={"Authorization": auth_header}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        # Non-fatal: the order is already placed and stock already adjusted.
        pass