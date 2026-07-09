import requests
from flask import current_app

REQUEST_TIMEOUT = 5


class ViewServiceUnavailable(Exception):
    pass


class InsufficientStock(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def decrement_stock(product_id, quantity, auth_header):
    url = f"{current_app.config['VIEW_SERVICE_URL']}/products/{product_id}/stock"
    try:
        resp = requests.patch(
            url, json={"quantity": quantity},
            headers={"Authorization": auth_header}, timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException:
        raise ViewServiceUnavailable()

    if resp.status_code == 409:
        raise InsufficientStock(resp.json().get("error", "Insufficient stock."))

    resp.raise_for_status()
    return resp.json()


def restock(product_id, quantity, auth_header):
    """Best-effort rollback if checkout fails partway through."""
    url = f"{current_app.config['VIEW_SERVICE_URL']}/products/{product_id}/restock"
    try:
        requests.post(
            url, json={"quantity": quantity},
            headers={"Authorization": auth_header}, timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException:
        pass