import asyncio
import sys
from asyncio.tasks import Task
import logging
from typing import List
from webserver import webserver

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logger = logging.getLogger(__name__)

all_tasks: List[Task] = []

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            all_tasks.append(tg.create_task(webserver.serve()))
    except asyncio.CancelledError:
        logger.info("Received SIGTERM. Cleaning up...")
        [task.cancel() for task in all_tasks]
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
