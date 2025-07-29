import os
from fastapi import FastAPI
import uvicorn

PORT = int(os.getenv("PORT", 5500))
PAIRS = os.getenv("PAIRS")

app = FastAPI()

@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "pairs": PAIRS
    }

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
