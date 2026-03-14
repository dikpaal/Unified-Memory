import sqlite3
from datetime import datetime
from typing import List


class SQLiteDatabase:

    def __init__(self, db_path: str = "memories.db"):
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS memories(
            id TEXT PRIMARY KEY,
            memory TEXT NOT NULL,
            hash TEXT NOT NULL,
            platform TEXT NOT NULL,
            synced_at INTEGER NOT NULL
        )
        """
        self.cursor.execute(query)

        # Important index for fast queries
        self.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_platform_time
        ON memories(platform, synced_at)
        """)

        self.connection.commit()

    def add_memory(
        self,
        memory_id: str,
        memory: str,
        memory_hash: str,
        platform: str,
        synced_at: int
    ):
        query = """
        INSERT OR REPLACE INTO memories
        (id, memory, hash, platform, synced_at)
        VALUES (?, ?, ?, ?, ?)
        """

        self.cursor.execute(query, (
            memory_id,
            memory,
            memory_hash,
            platform,
            synced_at
        ))

        self.connection.commit()

    def load_memories(
        self,
        target_platforms: List[str],
        target_timestamp: int
    ):
        """
        Retrieve memories from platforms after timestamp
        """

        placeholders = ",".join(["?"] * len(target_platforms))

        query = f"""
            SELECT *
            FROM memories
            WHERE platform IN ({placeholders})
            AND synced_at >= ?
            ORDER BY synced_at
        """

        params = target_platforms + [target_timestamp]

        self.cursor.execute(query, params)

        return self.cursor.fetchall()
    
    def latest_timestamp(self, platform: str):
        """
        Returns the latest timestamp for platform
        """

        query = """
        SELECT MAX(synced_at) FROM memories WHERE platform = ?
        """

        self.cursor.execute(query, (platform,))
        result = self.cursor.fetchone()[0]

        return result or 0