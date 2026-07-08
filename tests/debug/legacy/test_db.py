"""
Quick sanity check for async database configuration.
Run with: python test_db.py
"""

import asyncio
from backend.config.database import engine, AsyncSessionLocal
from sqlalchemy import text

async def test_connection():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1 as test"))
            value = result.scalar()
            print(f"✅ Connection successful – query returned: {value}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_engine_pool():
    """Check that the engine can acquire and release a connection."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Engine pool works – PostgreSQL version: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Engine pool test failed: {e}")
        return False

async def main():
    print("Testing async database configuration...\n")
    conn_ok = await test_connection()
    pool_ok = await test_engine_pool()
    if conn_ok and pool_ok:
        print("\n All tests passed. Async DB is ready.")
    else:
        print("\n Some tests failed. Check your DATABASE_URL and PostgreSQL service.")
    await engine.dispose()  # Clean shutdown

if __name__ == "__main__":
    asyncio.run(main())
