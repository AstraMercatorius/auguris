from fastapi import FastAPI
import uvicorn
from config import Config

config = Config()
app = FastAPI()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

def get_webserver():
    return uvicorn.Server(
            uvicorn.Config(
                app,
                host="0.0.0.0",
                port=config.port,
                log_level="info",
                loop="asyncio"
                )
            )
