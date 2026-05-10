import asyncio
import json

from app.core.database import async_session
from app.services.seed import reset_and_seed_demo_data


async def _run() -> None:
    async with async_session() as db:
        stats = await reset_and_seed_demo_data(db)

    print("Full seed completed.")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(_run())
