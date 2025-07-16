import asyncio
import sys
from asyncio.tasks import Task
import logging
from typing import List
from model_manager import ModelManager
from service import PredictionService
from webserver import webserver

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logger = logging.getLogger(__name__)

all_tasks: List[Task] = []

async def shutdown():
    logger.info("Shutdown initiated.")
    [task.cancel() for task in all_tasks]

async def main():
    predictionService = PredictionService()
    model_manager = ModelManager()
    try:
        async with asyncio.TaskGroup() as tg:
            all_tasks.append(tg.create_task(webserver.serve()))
            all_tasks.append(tg.create_task(model_manager.watch_models()))
            all_tasks.append(tg.create_task(predictionService.start()))
    except asyncio.CancelledError:
        logger.info("Received SIGTERM. Cleaning up...")
        await shutdown()
    finally:
        logger.info("Main exiting.")

if __name__ == "__main__":
    asyncio.run(main())
