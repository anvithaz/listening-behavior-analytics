import sqlite3
conn = sqlite3.connect("music.db")
cur = conn.cursor()
cur.execute("""
    SELECT 
        cohort_month,
        play_month,
        COUNT(*) as plays
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

for row in cur.fetchall():
    print(row)

