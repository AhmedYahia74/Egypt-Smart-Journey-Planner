from config_helper import get_db_params
from fastapi import HTTPException
import psycopg2
from psycopg2 import pool
import logging
from contextlib import asynccontextmanager
import asyncio

logger = logging.getLogger(__name__)

# Get database parameters
DB_PARAMS = get_db_params()
DB_PARAMS.update({
    'sslmode': 'require',
    'connect_timeout': 100
})

# Create a single connection pool for all APIs
try:
    connection_pool = pool.ThreadedConnectionPool(
        minconn=5,
        maxconn=20,
        **DB_PARAMS
    )
except Exception as e:
    logger.error(f"Failed to create connection pool: {str(e)}")
    raise

@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool with retry logic."""
    conn = None
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            conn = connection_pool.getconn()
            # Test the connection
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            yield conn
            break
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if conn:
                try:
                    connection_pool.putconn(conn, close=True)
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
                    connection_pool.putconn(conn, close=True)
                except:
                    pass
            raise HTTPException(status_code=500, detail="Internal server error")
        finally:
            if conn:
                try:
                    connection_pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}") 