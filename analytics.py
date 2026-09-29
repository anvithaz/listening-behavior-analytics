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
    RFM segmentation per artist, adapted for listening data:
      Recency   = days between the artist's last play and the newest play in the
                  dataset (snapshot date), so results don't drift with today's date
      Frequency = total play count
      Monetary  = total minutes listened (stands in for 'value' in classic RFM)

    Each metric is scored 1-3 from its CUME_DIST (3 = best), then artists are
    labelled. Tied values get the same score, unlike NTILE, which splits ties
    arbitrarily. Three bands instead of five because the catalog is small.
    """
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        WITH rfm AS (
            SELECT
                ar.name AS artist,
                CAST((SELECT julianday(MAX(played_at)) FROM plays) - julianday(MAX(p.played_at)) AS INTEGER) AS recency_days,
                COUNT(*) AS frequency,
                SUM(p.ms_played) / 60000.0 AS monetary_minutes
            FROM plays p
            JOIN tracks t ON p.track_id = t.track_id
            JOIN artists ar ON t.artist_id = ar.artist_id
            GROUP BY ar.name
        ),
        ranked AS (
            SELECT *,
                CUME_DIST() OVER (ORDER BY recency_days DESC)    AS r_pr,
                CUME_DIST() OVER (ORDER BY frequency ASC)        AS f_pr,
                CUME_DIST() OVER (ORDER BY monetary_minutes ASC) AS m_pr
            FROM rfm
        ),
        scored AS (
            SELECT *,
                CASE WHEN r_pr > 0.66 THEN 3 WHEN r_pr > 0.33 THEN 2 ELSE 1 END AS r_score,
                CASE WHEN f_pr > 0.66 THEN 3 WHEN f_pr > 0.33 THEN 2 ELSE 1 END AS f_score,
                CASE WHEN m_pr > 0.66 THEN 3 WHEN m_pr > 0.33 THEN 2 ELSE 1 END AS m_score
            FROM ranked
        )
        SELECT artist, recency_days, frequency, monetary_minutes,
               r_score, f_score, m_score,
               CASE
                   WHEN r_score = 3 AND f_score + m_score >= 5 THEN 'Champion'
                   WHEN r_score = 3                            THEN 'Recent'
                   WHEN r_score = 1 AND f_score + m_score >= 5 THEN 'At Risk'
                   WHEN r_score = 1                            THEN 'Lapsed'
                   ELSE 'Steady'
               END AS segment
        FROM scored
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
            "r_score": r[4],
            "f_score": r[5],
            "m_score": r[6],
            "segment": r[7],
        }
        for r in rows
    ]


if __name__ == "__main__":
    print("Top artists:", top_artists())
    print()
    print("RFM:", artist_rfm())
