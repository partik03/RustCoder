"""Minimal Flask web application."""

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def hello():
    """Return a simple greeting."""
    return "Hello, World!"


@app.route("/greet/<name>")
def greet(name: str):
    """Greet a specific person."""
    return f"Hello, {name}!"


@app.route("/api/status")
def status():
    """Return API status as JSON."""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "message": "Flask app is running"
    })


@app.route("/api/echo", methods=["POST"])
def echo():
    """Echo back the posted data."""
    data = request.get_json()
    return jsonify({
        "received": data,
        "type": "echo"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

