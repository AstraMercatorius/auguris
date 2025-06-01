import asyncio
import sys
from asyncio.tasks import Task
import logging
from typing import List
from webserver import get_webserver
from service import FeatureEngineeringService

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

all_tasks: List[Task] = []


async def shutdown():
    logger.info("Shutdown initiated.")
    [task.cancel() for task in all_tasks]

async def main():
    webserver = get_webserver()
    featuresService = FeatureEngineeringService()
    
    try:
        async with asyncio.TaskGroup() as tg:
            all_tasks.append(tg.create_task(webserver.serve()))
            all_tasks.append(tg.create_task(featuresService.start()))
    except asyncio.CancelledError:
        logger.info("Main received cancellation.")
        await shutdown()
    finally:
        logger.info("Main exiting.")

if __name__ == "__main__":
    asyncio.run(main())
