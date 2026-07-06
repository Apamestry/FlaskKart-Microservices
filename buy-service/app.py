import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"service": "buy-service", "status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5004))
    app.run(host="0.0.0.0", port=port, debug=True)
