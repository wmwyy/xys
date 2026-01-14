import sqlite3
from pathlib import Path
from typing import List, Tuple

DB_PATH = Path(__file__).parent.parent / "data" / "leaderboard.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS leaderboard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        score INTEGER NOT NULL,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
    conn.commit()
    conn.close()

def add_score(name: str, score: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO leaderboard (name, score) VALUES (?,?)", (name, int(score)))
    conn.commit()
    conn.close()

def top_n(n: int = 10) -> List[Tuple]:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name, score, ts FROM leaderboard ORDER BY score DESC, ts ASC LIMIT ?", (n,))
    rows = c.fetchall()
    conn.close()
    return rows

init_db()

