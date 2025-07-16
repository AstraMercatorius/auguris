from fastapi import FastAPI
import uvicorn
from config import Config

_config = Config()
app = FastAPI()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


webserver = uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=_config.port)
        )
