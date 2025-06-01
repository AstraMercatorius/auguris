import os
from fastapi import FastAPI
import uvicorn

PORT = int(os.getenv("PORT", 5500))

app = FastAPI()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

def get_webserver():
    return uvicorn.Server(
            uvicorn.Config(
                app,
                host="0.0.0.0",
                port=PORT,
                log_level="info",
                loop="asyncio"
                )
            )
