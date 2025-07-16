import asyncio
import os
import sys
from nats.errors import TimeoutError
from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.errors import BucketNotFoundError
from nats.js.object_store import ObjectStore

from config import Config

TMP_DIR = "/tmp/neural-trade/models"

class ModelManager:
    def __init__(self) -> None:
        self.nc = Client()
        self.js: JetStreamContext
        self._config = Config()
        self.object_store: ObjectStore
        self.nats_server = self._config.nats_url
        self.bucket_name = self._config.model_storage
        self.run_watcher = self._config.run_model_watcher

    async def connect_nats(self):
        await self.nc.connect(self.nats_server)
        self.js = self.nc.jetstream()

    async def ensure_bucket(self):
        try:
            self.object_store = await self.js.object_store(self.bucket_name)
        except BucketNotFoundError:
            self.object_store = await self.js.create_object_store(self.bucket_name)

    async def store_file(self, modelName: str):
        filename = f"{TMP_DIR}/{modelName}"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, mode="wb") as write_file:
            model_file = await self.object_store.get(modelName)
            write_file.write(model_file.data) # type: ignore
            write_file.close()

    async def get_models(self):
        models = await self.object_store.list()
        
        if(len(models) == 0):
            raise Exception("H5 Models not found in the bucket. Exiting")
        
        for model in models:
            await self.store_file(model.name)

    async def init_nats_connections(self):
        try:
            await self.connect_nats()
            await self.ensure_bucket()
        except Exception as e:
            print(f"Exception found {e}.\nExiting.")
            sys.exit(1)

    async def watch_models(self):
        await self.init_nats_connections()
        if not self.run_watcher:
            await self.get_models()
            print(f"Skipping the model object store watcher.")
            return

        object_watcher = await self.object_store.watch(include_history=False)
        while True:
            try:
                modelObject = await object_watcher.updates(timeout=30)
                if not modelObject:
                    continue
                
                if modelObject.deleted:
                    continue

                await self.store_file(modelObject.name)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                return
