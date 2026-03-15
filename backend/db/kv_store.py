from datetime import datetime, timezone
from typing import List
from collections import defaultdict
import sqlite3
import json
import os
from uuid import UUID

from models.models import Memory

class KVStore:

    def __init__(self, db_path: str = None):
        """
        SQLite-backed KV store for memories
        key: platform
        value: (Memory, timestamp)
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "unified_memory.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                platform TEXT NOT NULL CHECK(platform IN ('chatgpt', 'claude')),
                memory TEXT NOT NULL,
                metadata TEXT,
                timestamp REAL NOT NULL
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform_timestamp ON memories(platform, timestamp)")

        conn.commit()
        conn.close()
        
    def add_memory(self, platform: str, memory: Memory):
        """
        Add memory for `platform` with current timestamp
        """
        if platform not in {'chatgpt', 'claude'}:
            raise ValueError("Invalid platform")

        timestamp = datetime.now(timezone.utc).timestamp()
        metadata_json = json.dumps(memory.metadata) if memory.metadata else None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (memory_id, platform, memory, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
            (str(memory.memory_id), platform, memory.memory, metadata_json, timestamp)
        )
        conn.commit()
        conn.close()
        
    def get_memories(self, platform: str, timestamp: datetime) -> List[Memory]:
        """
        Returns the memories for a platform after `timestamp`
        """
        if platform not in {'chatgpt', 'claude'}:
            raise ValueError("Invalid platform")

        # Handle datetime.min (year 1) which can't convert to Unix timestamp
        # Use a very low value to get all memories
        if timestamp == datetime.min:
            ts_unix = -1e10
        else:
            ts_unix = timestamp.timestamp()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT memory_id, memory, metadata FROM memories WHERE platform = ? AND timestamp >= ? ORDER BY timestamp ASC",
            (platform, ts_unix)
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            Memory(
                memory_id=UUID(row[0]),
                memory=row[1],
                metadata=json.loads(row[2]) if row[2] else None
            )
            for row in rows
        ]
    
    def get_all_memories(self):
        """
        Returns all memories in the original dict format
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT platform, memory_id, memory, metadata, timestamp FROM memories ORDER BY platform, timestamp ASC"
        )
        rows = cursor.fetchall()
        conn.close()

        result = defaultdict(list)
        for row in rows:
            platform = row[0]
            memory = Memory(
                memory_id=UUID(row[1]),
                memory=row[2],
                metadata=json.loads(row[3]) if row[3] else None
            )
            dt = datetime.fromtimestamp(row[4], tz=timezone.utc)
            result[platform].append((memory, dt))

        return result