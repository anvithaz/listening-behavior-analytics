"""
Analytics queries for Apple Music listening history — cohort retention
and RFM-style artist segmentation, all computed via SQL (not pandas).
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "music.db")


def _connect():
    return sqlite3.connect(DB_PATH)


def top_artists():
    """Total play count and average listen duration per artist."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT ar.name, COUNT(*) as play_count, AVG(p.ms_played) / 1000.0 as avg_seconds
        FROM plays p
        JOIN tracks t ON p.track_id = t.track_id
        JOIN artists ar ON t.artist_id = ar.artist_id
        GROUP BY ar.name
        ORDER BY play_count DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [{"artist": r[0], "play_count": r[1], "avg_seconds": round(r[2], 1)} for r in rows]


def cohort_retention():
    """
    For each track's first-play month (its cohort), how many plays happened
    in each subsequent month. Same pattern as retention_1/retention_7 in the
    A/B test project, applied to listening behavior instead of game retention.
    """
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT cohort_month, play_month, COUNT(*) as plays
        FROM (
            SELECT
                t.title,
                strftime('%Y-%m', p.played_at) as play_month,
                (SELECT strftime('%Y-%m', MIN(p2.played_at))
                 FROM plays p2 WHERE p2.track_id = t.track_id) as cohort_month
            FROM plays p
            JOIN tracks t ON p.track_id = t.track_id
        )
        GROUP BY cohort_month, play_month
        ORDER BY cohort_month, play_month
    """)
    rows = cur.fetchall()
    conn.close()
    return [{"cohort_month": r[0], "play_month": r[1], "plays": r[2]} for r in rows]


def artist_rfm():
    """
    RFM-style segmentation per artist, adapted for listening data:
      Recency  = days since last play (lower = more recently listened to)
      Frequency = total play count
      Monetary  = total minutes listened (stands in for 'value' in classic RFM)
    """
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            ar.name,
            CAST(julianday('now') - julianday(MAX(p.played_at)) AS INTEGER) as recency_days,
            COUNT(*) as frequency,
            SUM(p.ms_played) / 60000.0 as monetary_minutes
        FROM plays p
        JOIN tracks t ON p.track_id = t.track_id
        JOIN artists ar ON t.artist_id = ar.artist_id
        GROUP BY ar.name
        ORDER BY monetary_minutes DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "artist": r[0],
            "recency_days": r[1],
            "frequency": r[2],
            "monetary_minutes": round(r[3], 1),
        }
        for r in rows
    ]


if __name__ == "__main__":
    print("Top artists:", top_artists())
    print()
    print("RFM:", artist_rfm())
