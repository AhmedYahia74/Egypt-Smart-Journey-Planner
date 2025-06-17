from config_helper import get_db_params
import psycopg2
from psycopg2 import pool
import logging
from contextlib import asynccontextmanager
from fastapi import HTTPException
import asyncio
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _pool = None
    _last_connection_attempt = 0
    _connection_timeout = 30  # seconds
    _max_retries = 3
    _retry_delay = 1  # seconds

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
            DB_Prams.update({
                'sslmode': 'require',
                'connect_timeout': 10,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            })
            
            self._pool = pool.ThreadedConnectionPool(
                minconn=1,  # Start with fewer connections
                maxconn=10,  # Limit max connections
                **DB_Prams
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {str(e)}")
            self._pool = None
            raise

    def _validate_connection(self, conn):
        """Validate if a connection is still active."""
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception:
            return False

    def _get_connection_with_retry(self):
        """Get a connection from the pool with retry logic."""
        current_time = time.time()
        
        # If we've tried too recently, wait
        if current_time - self._last_connection_attempt < self._retry_delay:
            time.sleep(self._retry_delay)
        
        self._last_connection_attempt = current_time
        
        for attempt in range(self._max_retries):
            try:
                conn = self._pool.getconn()
                if self._validate_connection(conn):
                    return conn
                else:
                    self._pool.putconn(conn, close=True)
                    raise psycopg2.OperationalError("Connection validation failed")
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt == self._max_retries - 1:
                    raise
                time.sleep(self._retry_delay * (2 ** attempt))
        
        raise psycopg2.OperationalError("Failed to get valid connection after retries")

    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool with retry logic."""
        conn = None
        try:
            conn = self._get_connection_with_retry()
            yield conn
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection error: {str(e)}")
            # Try to reinitialize the pool if we get connection errors
            if self._pool:
                try:
                    self._pool.closeall()
                except:
                    pass
                self._pool = None
                self._initialize_pool()
            raise HTTPException(status_code=503, detail="Database connection failed after multiple attempts")
        except Exception as e:
            logger.error(f"Unexpected database error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        finally:
            if conn:
                try:
                    self._pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}")
                    try:
                        conn.close()
                    except:
                        pass

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