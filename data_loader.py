"""
Loads Apple Music play history into a proper relational SQLite schema —
NOT one flat table. Splits into tracks, artists, and plays, so the SQL
queries later actually need joins (this is the point of the exercise).
"""
import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "music.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "apple_music_history.csv")


def build_db(csv_path=CSV_PATH, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS plays;
        DROP TABLE IF EXISTS tracks;
        DROP TABLE IF EXISTS artists;

        CREATE TABLE artists (
            artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE tracks (
            track_id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            album TEXT,
            track_length_ms INTEGER,
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        );

        CREATE TABLE plays (
            play_id INTEGER PRIMARY KEY,
            track_id INTEGER NOT NULL,
            played_at TEXT NOT NULL,
            ms_played INTEGER,
            device TEXT,
            FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        );
    """)

    artist_ids = {}   # name -> artist_id
    track_ids = {}     # (artist, title) -> track_id

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist = row["artist"]
            title = row["track"]

            if artist not in artist_ids:
                cur.execute("INSERT INTO artists (name) VALUES (?)", (artist,))
                artist_ids[artist] = cur.lastrowid

            key = (artist, title)
            if key not in track_ids:
                cur.execute(
                    "INSERT INTO tracks (artist_id, title, album, track_length_ms) VALUES (?, ?, ?, ?)",
                    (artist_ids[artist], title, row["album"], int(row["track_length_ms"])),
                )
                track_ids[key] = cur.lastrowid

            cur.execute(
                "INSERT INTO plays (play_id, track_id, played_at, ms_played, device) VALUES (?, ?, ?, ?, ?)",
                (int(row["play_id"]), track_ids[key], row["timestamp"], int(row["ms_played"]), row["device"]),
            )

    conn.commit()
    print(f"Loaded {len(artist_ids)} artists, {len(track_ids)} tracks, into {db_path}")
    conn.close()


if __name__ == "__main__":
    build_db()
