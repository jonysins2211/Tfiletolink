from flask import Flask, request, jsonify
from Thunder.utils.shortener import resolve_token
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "ML Redirect Server Running"

@app.route("/resolve")
def resolve():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "missing"}), 400

    url = resolve_token(token)
    if not url:
        return jsonify({"error": "invalid"}), 403

    return jsonify({"url": url})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
