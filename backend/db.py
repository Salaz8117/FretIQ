"""
FretIQ App - Database Module
Async SQLite with aiosqlite, migrations, and connection pooling.
"""
import asyncio
import aiosqlite
import os
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from config import get_settings

settings = get_settings()

# Database file path
DB_DIR = Path(__file__).parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "music_chords.db"

# Connection pool
_pool: Optional[asyncio.Queue] = None
_pool_size = 5


async def init_db() -> None:
    """Initialize database with schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Search history table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                song_name TEXT NOT NULL,
                artist TEXT,
                instruments TEXT NOT NULL,
                result_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Favorites table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                song_name TEXT NOT NULL,
                artist TEXT,
                result_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, song_name, artist)
            )
        """)
        
        # Feedback table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                result_id TEXT NOT NULL,
                song_name TEXT NOT NULL,
                artist TEXT,
                rating INTEGER NOT NULL,
                comment TEXT,
                corrections TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
            )
        """)
        
        # Indexes for performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id)")
        
        await db.commit()


async def get_connection() -> aiosqlite.Connection:
    """Get a database connection from pool or create new."""
    global _pool
    
    if _pool is None:
        _pool = asyncio.Queue(maxsize=_pool_size)
        for _ in range(_pool_size):
            conn = await aiosqlite.connect(DB_PATH)
            conn.row_factory = aiosqlite.Row
            await _pool.put(conn)
    
    try:
        conn = _pool.get_nowait()
    except asyncio.QueueEmpty:
        conn = await aiosqlite.connect(DB_PATH)
        conn.row_factory = aiosqlite.Row
    
    return conn


async def release_connection(conn: aiosqlite.Connection) -> None:
    """Return connection to pool."""
    global _pool
    if _pool and not _pool.full():
        await _pool.put(conn)
    else:
        await conn.close()


@asynccontextmanager
async def db_connection():
    """Context manager for database connections."""
    conn = await get_connection()
    try:
        yield conn
    finally:
        await release_connection(conn)


async def execute_query(query: str, params: tuple = ()) -> list:
    """Execute a query and return results."""
    async with db_connection() as conn:
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def execute_one(query: str, params: tuple = ()) -> Optional[dict]:
    """Execute a query and return single result."""
    async with db_connection() as conn:
        cursor = await conn.execute(query, params)
        row = await cursor.fetchone()
        return dict(row) if row else None


async def execute_insert(query: str, params: tuple = ()) -> int:
    """Execute an insert and return last row ID."""
    async with db_connection() as conn:
        cursor = await conn.execute(query, params)
        await conn.commit()
        return cursor.lastrowid


async def execute_update(query: str, params: tuple = ()) -> int:
    """Execute an update/delete and return affected rows."""
    async with db_connection() as conn:
        cursor = await conn.execute(query, params)
        await conn.commit()
        return cursor.rowcount


async def close_pool() -> None:
    """Close all connections in pool."""
    global _pool
    if _pool:
        while not _pool.empty():
            conn = await _pool.get()
            await conn.close()
        _pool = None