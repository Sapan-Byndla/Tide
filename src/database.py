import contextlib
import logging
from typing import AsyncGenerator, Generator
import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.asyncpg import register_vector
from src.config import config

logger = logging.getLogger("tide.database")

# --- Asyncpg (FastAPI & Async code) ---
_pool: asyncpg.Pool = None

async def init_connection(conn):
    try:
        await register_vector(conn)
    except Exception as e:
        logger.warning(f"Could not register pgvector type with connection: {e}")

async def init_db_pool():
    global _pool
    if _pool is None:
        db_url = config.database_url
        if not db_url:
            raise ValueError("Database connection URL not configured.")
        
        logger.info("Initializing asyncpg database pool...")
        # Enable connection pooling
        _pool = await asyncpg.create_pool(
            dsn=db_url,
            min_size=config.database_pool_min,
            max_size=config.database_pool_max,
            ssl="require",
            init=init_connection
        )

async def close_db_pool():
    global _pool
    if _pool is not None:
        logger.info("Closing asyncpg database pool...")
        await _pool.close()
        _pool = None

@contextlib.asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    global _pool
    if _pool is None:
        await init_db_pool()
    
    async with _pool.acquire() as conn:
        yield conn


# --- Psycopg2 (Synchronous Scripts / Background Jobs) ---
@contextlib.contextmanager
def get_sync_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    db_url = config.database_url
    if not db_url:
        raise ValueError("Database connection URL not configured.")
    
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        yield conn
    except Exception as e:
        logger.error(f"Synchronous database connection error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

@contextlib.contextmanager
def get_sync_cursor() -> Generator[psycopg2.extensions.cursor, None, None]:
    with get_sync_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
            conn.commit()
