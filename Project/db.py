import sqlite3
import config

def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def query(sql, params=None, one=False):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    rows = cur.fetchone() if one else cur.fetchall()
    conn.close()
    if rows is None:
        return None
    if one:
        return dict(rows) if rows else None
    return [dict(r) for r in rows]

def execute(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    conn.close()
