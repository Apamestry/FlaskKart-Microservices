import requests
from flask import Blueprint, request, jsonify, current_app, Response

proxy_bp = Blueprint("proxy", __name__)

REQUEST_TIMEOUT = 10  # seconds

# Maps the path prefix a client hits on the Gateway to the config key
# holding that service's internal URL. Paths are forwarded 1:1 (same
# suffix), only the host:port changes - so /cart/add on the Gateway
# becomes http://cart-service:5003/cart/add, no path rewriting needed.
SERVICE_MAP = {
    "products": "VIEW_SERVICE_URL",
    "search": "SEARCH_SERVICE_URL",
    "cart": "CART_SERVICE_URL",
    "buy": "BUY_SERVICE_URL",
}


def _forward(service_key, path):
    base_url = current_app.config[SERVICE_MAP[service_key]]
    url = f"{base_url}/{path}" if path else base_url

    headers = {}
    if "Authorization" in request.headers:
        headers["Authorization"] = request.headers["Authorization"]
    if request.content_type:
        headers["Content-Type"] = request.content_type

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.args,
            data=request.get_data(),  # forward the raw body untouched
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException:
        return jsonify({"error": f"The {service_key} service is unavailable."}), 503

    return Response(
        resp.content,
        status=resp.status_code,
        content_type=resp.headers.get("Content-Type", "application/json"),
    )


@proxy_bp.route("/products", methods=["GET", "POST"], strict_slashes=False)
@proxy_bp.route("/products/<path:subpath>", methods=["GET", "POST", "PATCH", "DELETE"])
def proxy_products(subpath=""):
    path = "products" + (f"/{subpath}" if subpath else "")
    return _forward("products", path)


@proxy_bp.route("/search", methods=["GET"], strict_slashes=False)
@proxy_bp.route("/search/<path:subpath>", methods=["GET"])
def proxy_search(subpath=""):
    path = "search" + (f"/{subpath}" if subpath else "")
    return _forward("search", path)


@proxy_bp.route("/cart", methods=["GET"], strict_slashes=False)
@proxy_bp.route("/cart/<path:subpath>", methods=["GET", "POST", "PATCH", "DELETE"])
def proxy_cart(subpath=""):
    path = "cart" + (f"/{subpath}" if subpath else "")
    return _forward("cart", path)


@proxy_bp.route("/buy", methods=["GET"], strict_slashes=False)
@proxy_bp.route("/buy/<path:subpath>", methods=["GET", "POST"])
def proxy_buy(subpath=""):
    path = "buy" + (f"/{subpath}" if subpath else "")
    return _forward("buy", path)