from datetime import datetime, timezone
from typing import List
from collections import defaultdict
from uuid import UUID
import numpy as np
import sqlite3
import json
import os

from backend.models.models import Memory

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
        self.cleanup_old_memories()

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
                timestamp REAL NOT NULL,
                embedding BLOB
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform_timestamp ON memories(platform, timestamp)")

        # Migration for existing DBs: add embedding column if missing
        cursor.execute("PRAGMA table_info(memories)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'embedding' not in columns:
            cursor.execute("ALTER TABLE memories ADD COLUMN embedding BLOB")

        conn.commit()
        conn.close()

    def cleanup_old_memories(self, hours: int = 24):
        """Delete memories older than specified hours"""
        cutoff_timestamp = datetime.now(timezone.utc).timestamp() - (hours * 3600)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE timestamp < ?", (cutoff_timestamp,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count
        
    def add_memory(self, platform: str, memory: Memory, embedding: list[float]):
        """
        Add memory for `platform` with current timestamp and embedding
        """
        print("START OF ADD MEMORY")
        if platform not in {'chatgpt', 'claude'}:
            raise ValueError("Invalid platform")

        timestamp = datetime.now(timezone.utc).timestamp()
        metadata_json = json.dumps(memory.metadata) if memory.metadata else None
        embedding_blob = json.dumps(embedding)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        print("JUST BEFORE INSERT INTO STATEMENT")
        cursor.execute(
            "INSERT INTO memories (memory_id, platform, memory, metadata, timestamp, embedding) VALUES (?, ?, ?, ?, ?, ?)",
            (str(memory.memory_id), platform, memory.memory, metadata_json, timestamp, embedding_blob)
        )
        print("DONE!!!!!!")
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
    
    def perform_vector_search(self, embedding: List[float], top_k: int = 2, threshold: float = 0.87) -> List[tuple[str, str, float]]:
        """
        Returns list of memories based on the filers set
        """
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT platform, memory_id, memory, metadata, embedding, timestamp FROM memories ORDER BY platform, timestamp ASC"
        )
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        
        for row in rows:
            row_embedding = np.array(json.loads(row[4]))
            score = self._cosine_similarity(embedding, row_embedding)
            results.append(
                (UUID(row[1]), row[2], score)
            )
        
        print(results)
        
        results.sort(key=lambda x: x[2], reverse=True)
        
        results = results[:top_k]
        return [r for r in results if r[2] >= threshold]
        
        
    def _cosine_similarity(self, a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))