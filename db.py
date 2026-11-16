import json
import os
import sqlite3

table_name = "data"
VALID_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


with _connect() as _init_conn:
    _init_conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
            user_id INTEGER NOT NULL,
            english_level TEXT NOT NULL CHECK (english_level IN ("A1", "A2", "B1", "B2", "C1", "C2")),
            analyse_data TEXT NOT NULL
        )
    """)


def save_video(video_id, url, title, level, channel="", duration_label="", result=None):
    """Upsert video analysis (or compact metadata) into data table, deduplicated by videoId."""
    if level not in VALID_LEVELS:
        return
    record = dict(result) if isinstance(result, dict) else {}
    record.update({
        "videoId": video_id,
        "url": url,
        "title": title,
        "level": level,
        "channel": channel,
        "durationLabel": duration_label,
    })
    payload = json.dumps(record, sort_keys=True)
    with _connect() as conn:
        conn.execute(
            "DELETE FROM data WHERE json_extract(analyse_data, '$.videoId') = ?",
            (video_id,),
        )
        conn.execute("INSERT INTO data VALUES (?, ?, json(?))", (0, level, payload))


def get_video_analysis(video_id):
    """Return cached full VideoAnalysisResult dict for video_id, or None."""
    with _connect() as conn:
        row = conn.execute(
            """SELECT analyse_data FROM data
               WHERE json_extract(analyse_data, '$.videoId') = ?
               ORDER BY rowid DESC LIMIT 1""",
            (video_id,),
        ).fetchone()
    if not row:
        return None
    data = json.loads(row[0])
    # Only treat as full cached analysis if metrics & detectedLevel exist
    if isinstance(data, dict) and "metrics" in data and "detectedLevel" in data:
        return data
    return None


def get_videos_by_level(level, limit=50):
    """Return up to `limit` unique saved videos matching `level` (or all if level=='ALL')."""
    if level == "ALL":
        query = (
            "SELECT analyse_data FROM data "
            "WHERE json_extract(analyse_data, '$.url') IS NOT NULL "
            "ORDER BY rowid DESC LIMIT ?"
        )
        params = (limit,)
    elif level in VALID_LEVELS:
        query = (
            "SELECT analyse_data FROM data "
            "WHERE english_level = ? AND json_extract(analyse_data, '$.url') IS NOT NULL "
            "ORDER BY rowid DESC LIMIT ?"
        )
        params = (level, limit)
    else:
        raise ValueError(f"Invalid CEFR level: {level}")
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    items = []
    for (raw,) in rows:
        d = json.loads(raw)
        vid = d.get("videoId")
        items.append({
            "videoId": vid,
            "url": d.get("url"),
            "title": d.get("title"),
            "level": d.get("level") or d.get("detectedLevel") or level,
            "channel": d.get("channel", ""),
            "durationLabel": d.get("durationLabel", ""),
            "thumbnailUrl": d.get("thumbnailUrl") or (f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else ""),
        })
    return items
