import os

import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)

VIEW_SERVICE_URL = os.getenv("VIEW_SERVICE_URL")
REQUEST_TIMEOUT = 5  # seconds


@app.route("/health")
def health():
    return jsonify({"service": "search-service", "status": "ok"})


@app.route("/search", methods=["GET"])
def search():
    """Forwards q/category query params to View Service's product listing.

    Search Service owns no data itself — it's a stateless layer that can be
    scaled independently under search-heavy load without touching the
    catalog's own database.
    """
    params = {}
    if request.args.get("q"):
        params["q"] = request.args.get("q")
    if request.args.get("category"):
        params["category"] = request.args.get("category")

    try:
        resp = requests.get(f"{VIEW_SERVICE_URL}/products", params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        return jsonify({"error": "View Service is unavailable."}), 503

    return jsonify(resp.json()), resp.status_code


@app.route("/search/categories", methods=["GET"])
def categories():
    try:
        resp = requests.get(f"{VIEW_SERVICE_URL}/products/categories", timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        return jsonify({"error": "View Service is unavailable."}), 503

    return jsonify(resp.json()), resp.status_code


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)