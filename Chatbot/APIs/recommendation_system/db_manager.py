from config_helper import get_db_params
import psycopg2
from psycopg2 import pool
import logging
from contextlib import asynccontextmanager
from fastapi import HTTPException
import asyncio

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pool is None:
            self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool with optimized settings."""
        try:
            DB_Prams = get_db_params()
            DB_Prams.update({'sslmode': 'require'})
            
            self._pool = pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                **DB_Prams
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {str(e)}")
            raise

    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool with retry logic."""
        conn = None
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                conn = self._pool.getconn()
                # Test the connection
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                yield conn
                break
            except psycopg2.OperationalError as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
                if conn:
                    try:
                        self._pool.putconn(conn, close=True)
                    except:
                        pass
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=503, detail="Database connection failed after multiple attempts")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            except Exception as e:
                logger.error(f"Unexpected database error: {str(e)}")
                if conn:
                    try:
                        self._pool.putconn(conn, close=True)
                    except:
                        pass
                raise HTTPException(status_code=500, detail="Internal server error")
            finally:
                if conn:
                    try:
                        self._pool.putconn(conn)
                    except Exception as e:
                        logger.error(f"Error returning connection to pool: {str(e)}")

    def close_pool(self):
        """Close all connections in the pool."""
        if self._pool:
            try:
                self._pool.closeall()
                logger.info("Database connection pool closed successfully")
            except Exception as e:
                logger.error(f"Error closing connection pool: {str(e)}")
            finally:
                self._pool = None

# Create a singleton instance
db_manager = DatabaseManager() 