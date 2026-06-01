"""SQLite persistence layer."""

import os
import sqlite3
import threading

from .models import Meeting, Room, default_rooms


class MeetingRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self.init_schema()
        self.seed_rooms()

    def close(self):
        with self._lock:
            self._conn.close()

    def init_schema(self):
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    floor INTEGER NOT NULL,
                    capacity INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organizer_name TEXT NOT NULL,
                    room_id INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    attendee_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES rooms(id)
                );

                CREATE INDEX IF NOT EXISTS idx_meetings_room_time
                    ON meetings(room_id, start_time, end_time);
                CREATE INDEX IF NOT EXISTS idx_meetings_organizer
                    ON meetings(organizer_name);
                """
            )
            self._conn.commit()

    def seed_rooms(self):
        with self._lock:
            for room in default_rooms():
                self._conn.execute(
                    """
                    INSERT OR IGNORE INTO rooms (id, name, floor, capacity)
                    VALUES (?, ?, ?, ?)
                    """,
                    (room.room_id, room.name, room.floor, room.capacity),
                )
            self._conn.commit()

    def save_user(self, username):
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO users (username) VALUES (?)",
                (username,),
            )
            self._conn.commit()

    def list_rooms(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, name, floor, capacity FROM rooms ORDER BY floor, capacity DESC, id"
            ).fetchall()
        return [self._row_to_room(row) for row in rows]

    def get_room_by_id(self, room_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name, floor, capacity FROM rooms WHERE id = ?",
                (room_id,),
            ).fetchone()
        return self._row_to_room(row) if row else None

    def get_room_by_name(self, room_name):
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name, floor, capacity FROM rooms WHERE name = ?",
                (room_name,),
            ).fetchone()
        return self._row_to_room(row) if row else None

    def add_meeting(self, organizer_name, room_id, topic, start_time, end_time, attendee_count):
        with self._lock:
            cursor = self._conn.execute(
                """
                INSERT INTO meetings
                    (organizer_name, room_id, topic, start_time, end_time, attendee_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (organizer_name, room_id, topic, start_time, end_time, attendee_count),
            )
            self._conn.commit()
            return cursor.lastrowid

    def find_meeting_by_id(self, meeting_id):
        with self._lock:
            row = self._conn.execute(
                self._meeting_select_sql() + " WHERE m.id = ?",
                (meeting_id,),
            ).fetchone()
        return self._row_to_meeting(row) if row else None

    def find_meetings_by_organizer(self, organizer_name):
        with self._lock:
            rows = self._conn.execute(
                self._meeting_select_sql() + " WHERE m.organizer_name = ? ORDER BY m.start_time",
                (organizer_name,),
            ).fetchall()
        return [self._row_to_meeting(row) for row in rows]

    def find_meetings_by_room(self, room_id):
        with self._lock:
            rows = self._conn.execute(
                self._meeting_select_sql() + " WHERE m.room_id = ? ORDER BY m.start_time",
                (room_id,),
            ).fetchall()
        return [self._row_to_meeting(row) for row in rows]

    def list_all_meetings(self):
        with self._lock:
            rows = self._conn.execute(
                self._meeting_select_sql() + " ORDER BY m.start_time, m.id"
            ).fetchall()
        return [self._row_to_meeting(row) for row in rows]

    def find_conflicts(self, room_id, start_time, end_time, exclude_meeting_id=None):
        params = [room_id, end_time, start_time]
        sql = (
            self._meeting_select_sql()
            + " WHERE m.room_id = ? AND ? > m.start_time AND ? < m.end_time"
        )
        if exclude_meeting_id is not None:
            sql += " AND m.id <> ?"
            params.append(exclude_meeting_id)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_meeting(row) for row in rows]

    def delete_meeting(self, meeting_id):
        with self._lock:
            cursor = self._conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            self._conn.commit()
            return cursor.rowcount > 0

    def _meeting_select_sql(self):
        return """
            SELECT
                m.id AS meeting_id,
                m.organizer_name,
                m.room_id,
                r.name AS room_name,
                m.topic,
                m.start_time,
                m.end_time,
                m.attendee_count
            FROM meetings m
            JOIN rooms r ON r.id = m.room_id
        """

    def _row_to_room(self, row):
        return Room(row["id"], row["name"], row["floor"], row["capacity"])

    def _row_to_meeting(self, row):
        return Meeting(
            row["meeting_id"],
            row["organizer_name"],
            row["room_id"],
            row["room_name"],
            row["topic"],
            row["start_time"],
            row["end_time"],
            row["attendee_count"],
        )
