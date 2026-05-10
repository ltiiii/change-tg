from __future__ import annotations

import asyncio

from exchange_bots.admin_bot import main as admin_main
from exchange_bots.client_bot import main as client_main


async def main() -> None:
    async with asyncio.TaskGroup() as task_group:
        task_group.create_task(client_main(handle_signals=False))
        task_group.create_task(admin_main(handle_signals=False))


if __name__ == "__main__":
    asyncio.run(main())
