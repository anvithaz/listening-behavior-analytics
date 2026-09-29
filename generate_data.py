"""
Generates a synthetic Apple Music-style play history CSV, shaped like the
real export you'll get from Apple (timestamp, track, artist, album, ms played).
Once your real export lands, swap this file out — same column structure.
"""
import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

# Your actual artists/tracks — building the catalog first
catalog = [
    ("Steve Lacy", "Bad Habit", "Gemini Rights"),
    ("Steve Lacy", "Dark Red", "Apollo XXI"),
    ("Steve Lacy", "Static", "Gemini Rights"),
    ("The Mamas & the Papas", "California Dreamin'", "If You Can Believe Your Eyes and Ears"),
    ("The Mamas & the Papas", "Monday, Monday", "If You Can Believe Your Eyes and Ears"),
    ("Jeff Buckley", "Hallelujah", "Grace"),
    ("Jeff Buckley", "Lover, You Should've Come Over", "Grace"),
    ("Jeff Buckley", "Grace", "Grace"),
    ("Michael Jackson", "Billie Jean", "Thriller"),
    ("Michael Jackson", "Human Nature", "Thriller"),
    ("Michael Jackson", "Smooth Criminal", "Bad"),
    ("The Velvet Underground", "Pale Blue Eyes", "The Velvet Underground"),
    ("The Velvet Underground", "Sunday Morning", "The Velvet Underground & Nico"),
    ("The Velvet Underground", "Pyramids", "White Light/White Heat"),  # placeholder pairing
]

# Simulate 9 months of listening history, players ramping up/down differently per artist
start_date = datetime(2025, 12, 1)
end_date = datetime(2026, 8, 30)
total_days = (end_date - start_date).days

rows = []
play_id = 1

# Give each track a "popularity curve" — some rediscovered later, some fading
for artist, track, album in catalog:
    # random number of plays for this track over the period, weighted per artist
    base_plays = random.randint(15, 60)
    # pick a "peak month" for this track — plays cluster around it
    peak_day = random.randint(0, total_days)
    for _ in range(base_plays):
        # plays cluster near peak_day using a rough normal-ish spread
        offset = int(random.gauss(0, 45))
        day_offset = max(0, min(total_days, peak_day + offset))
        play_date = start_date + timedelta(days=day_offset)
        play_date = play_date.replace(
            hour=random.randint(7, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )
        track_length_ms = random.randint(180000, 320000)
        # most plays are full listens, some are skips
        played_ms = track_length_ms if random.random() > 0.15 else random.randint(5000, track_length_ms)

        rows.append({
            "play_id": play_id,
            "timestamp": play_date.strftime("%Y-%m-%d %H:%M:%S"),
            "artist": artist,
            "track": track,
            "album": album,
            "ms_played": played_ms,
            "track_length_ms": track_length_ms,
            "device": random.choice(["iPhone", "MacBook", "iPad"]),
        })
        play_id += 1

rows.sort(key=lambda r: r["timestamp"])

os.makedirs("data", exist_ok=True)
with open("data/apple_music_history.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} plays across {len(catalog)} tracks -> data/apple_music_history.csv")
