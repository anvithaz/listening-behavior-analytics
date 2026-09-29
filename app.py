"""
Flask API for Apple Music listening analytics.

Endpoints:
  GET /                       -> dashboard
  GET /api/top-artists         -> play count + avg listen duration per artist
  GET /api/cohort-retention    -> cohort month x play month retention table
  GET /api/rfm                 -> Recency/Frequency/Monetary per artist
"""
import os
from flask import Flask, jsonify, send_from_directory

from analytics import top_artists, cohort_retention, artist_rfm

app = Flask(__name__)


@app.route("/", methods=["GET"])
def dashboard():
    return send_from_directory(os.path.dirname(__file__), "dashboard.html")


@app.route("/api/top-artists", methods=["GET"])
def api_top_artists():
    return jsonify(top_artists())


@app.route("/api/cohort-retention", methods=["GET"])
def api_cohort_retention():
    return jsonify(cohort_retention())


@app.route("/api/rfm", methods=["GET"])
def api_rfm():
    return jsonify(artist_rfm())


if __name__ == "__main__":
    app.run(debug=True, port=5002)
