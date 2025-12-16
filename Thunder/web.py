from flask import Flask, request, jsonify
from Thunder.utils.shortener import resolve_token

app = Flask(__name__)

@app.route("/")
def home():
    return "ML Files Redirect Server Running"

@app.route("/resolve")
def resolve():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "missing"}), 400

    url = resolve_token(token)
    if not url:
        return jsonify({"error": "invalid"}), 403

    return jsonify({"url": url})
