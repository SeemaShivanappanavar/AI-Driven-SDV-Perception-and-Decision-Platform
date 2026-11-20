import sqlite3
import json
import time
import os


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

DATABASE_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "sdv_history.db"
)


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():

    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )

    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=10000")

    return connection


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

def initialize_database():

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            signal TEXT NOT NULL,

            session_id TEXT,

            sequence_number INTEGER,

            received_at_ms INTEGER NOT NULL,

            payload TEXT NOT NULL

        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_session
        ON events(session_id)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_signal
        ON events(signal)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_received
        ON events(received_at_ms)
    """)

    connection.commit()
    connection.close()


# ==========================================================
# SAVE EVENT
# ==========================================================

def save_event(signal, data):

    if not isinstance(data, dict):
        return

    session_id = data.get("session_id")

    sequence_number = data.get("sequence_number")

    received_at_ms = int(time.time() * 1000)

    payload = json.dumps(data)

    connection = get_connection()

    try:

        connection.execute("""
            INSERT INTO events (
                signal,
                session_id,
                sequence_number,
                received_at_ms,
                payload
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            signal,
            session_id,
            sequence_number,
            received_at_ms,
            payload
        ))

        connection.commit()

    finally:

        connection.close()


# ==========================================================
# GET RECENT EVENTS
# ==========================================================

def get_recent_events(limit=100):

    connection = get_connection()

    try:

        cursor = connection.execute("""
            SELECT
                id,
                signal,
                session_id,
                sequence_number,
                received_at_ms,
                payload

            FROM events

            ORDER BY id DESC

            LIMIT ?
        """, (limit,))

        return cursor.fetchall()

    finally:

        connection.close()


# ==========================================================
# GET DATABASE STATISTICS
# ==========================================================

def get_database_statistics():

    connection = get_connection()

    try:

        cursor = connection.execute("""
            SELECT
                signal,
                COUNT(*)

            FROM events

            GROUP BY signal
        """)

        return dict(cursor.fetchall())

    finally:

        connection.close()
