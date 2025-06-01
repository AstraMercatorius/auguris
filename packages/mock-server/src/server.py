from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel
from typing import Dict, Any
import json

from mock_middleware import MockMiddleware, MockedResponse

app = FastAPI()
# Store mocks in a dict keyed by JSON-serialized filter objects
mocked_responses: Dict[str, MockedResponse] = {}

class MockConfiguration(BaseModel):
    filters: Dict[str, Any]
    response: Dict[str, Any]  # expects keys: body, headers (opt), status (opt)

@app.post("/mock")
async def configure_mock(cfg: MockConfiguration):
    # Create a MockedResponse object
    body = cfg.response.get("body")
    headers = cfg.response.get("headers")
    status = cfg.response.get("status", 200)
    mock_resp = MockedResponse(body=body, headers=headers, status=status)

    # Store under JSON key
    key = json.dumps(cfg.filters)
    mocked_responses[key] = mock_resp

    # Return summary of configured mocks
    return {
        "message": "Mocked response configured successfully",
        "mocks": [
            {
                "filters": json.loads(k),
                "response": {
                    "body": mr.body,
                    "headers": mr.headers,
                    "status": mr.status
                }
            }
            for k, mr in mocked_responses.items()
        ]
    }

@app.get("/mock")
async def list_mocks():
    return {
        "mocks": [
            {
                "filters": json.loads(k),
                "response": {
                    "body": mr.body,
                    "headers": mr.headers,
                    "status": mr.status
                }
            }
            for k, mr in mocked_responses.items()
        ]
    }

@app.delete("/mock")
async def clear_mocks():
    """
    Remove all mock configurations.
    """
    mocked_responses.clear()
    return {
        "message": "All mocks cleared successfully",
        "mocks": []
    }, status.HTTP_200_OK

# Mount the mock middleware
app.add_middleware(MockMiddleware, mocked_responses=mocked_responses)

# Fallback handler (like express’s res.sendStatus(200))
@app.middleware("http")
async def fallback_200(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 404:
        return Response(status_code=200)
    return response
