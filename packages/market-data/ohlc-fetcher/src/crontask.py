import asyncio
import logging
import os
from typing import Any, Awaitable, Callable, List
import schedule
from datetime import datetime

logger = logging.getLogger(__name__)

class SingletonMeta(type):
    _instances = {}

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self not in self._instances:
            instance = super().__call__(*args, **kwds)
            self._instances[self] = instance
        return self._instances[self]

class Crontask(metaclass=SingletonMeta):

    def __init__(self) -> None:
        self._running = False
        self._interval = int(os.getenv("CRON_SECONDS", 900))
        logger.info(f"Interval configured to {self._interval} seconds")
        self._subscribers: List[Callable[[], Awaitable[Any]]] = []

    def subscribe(self, listener: Callable[[], Awaitable[Any]]):
        logger.info(f"Subscribed new task: {listener.__name__}")
        self._subscribers.append(listener)

    def clear_subscribers(self) -> None:
        self._subscribers.clear()
    
    def set_interval(self, interval: int) -> None:
        self._interval = interval

    def _dispatch_tasks(self):
        if not self._subscribers:
            logger.debug("No subscribers to dispatch.")
            return
        
        logger.info(f"Dispatching {len(self._subscribers)} crontask subscribers at {datetime.now()}")
        asyncio.create_task(self._run_subscribers())
    
    async def _run_subscribers(self):
        await asyncio.gather(*(subscriber() for subscriber in self._subscribers), return_exceptions=True)

    async def start(self):
        if self._running:
            logger.warning("Crontask already started. Can't start it again.")
            return

        schedule.every(self._interval).seconds.do(self._dispatch_tasks)
        self._running = True

        try:
            while self._running:
                schedule.run_pending()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Crontask cancelled. Exiting task loop.")
            self.stop()
        finally:
            logger.info("Crontask finished cleanup")

    def stop(self):
        schedule.clear()
        self._running = False
