import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from backend.app.db.session import engine, async_session_factory

async def test():
    print("Engine URL:", engine.url)
    print("Testing engine.connect()...")
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT 1;"))
        print("Engine connected! SELECT 1 returned:", res.scalar())

    print("Testing async_session_factory()...")
    async with async_session_factory() as session:
        res_ep = await session.execute(text("SELECT count(*) FROM episodes;"))
        res_ch = await session.execute(text("SELECT count(*) FROM chunks;"))
        print(f"Episodes: {res_ep.scalar()} | Chunks: {res_ch.scalar()}")

if __name__ == "__main__":
    asyncio.run(test())
