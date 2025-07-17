from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Any, Dict, Optional
import json

class MockedResponse:
    def __init__(
        self,
        body: Any,
        headers: Optional[Dict[str, str]] = None,
        status: int = 200
    ):
        self.body = body
        self.headers = headers or {}
        self.status = status

class MockMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, mocked_responses: Dict[str, MockedResponse]):
        super().__init__(app)
        # keys are JSON-serialized filter dicts
        self.mocked_responses = mocked_responses

    async def dispatch(self, request: Request, call_next):
        # Attempt to find a matching mocked response
        for key, mock_resp in self.mocked_responses.items():
            filters = json.loads(key)
            path = filters.get("path")
            method = filters.get("method")
            headers = filters.get("headers") or {}

            # Check path and method
            if path and path != request.url.path:
                continue
            if method and method.upper() != request.method:
                continue

            # Check headers
            if headers:
                # all header filters must match exactly
                if not all(request.headers.get(k) == v for k, v in headers.items()):
                    continue

            # All filters passed → return mocked response
            return JSONResponse(
                content=mock_resp.body,
                status_code=mock_resp.status,
                headers=mock_resp.headers
            )

        # Otherwise continue to the next handler
        return await call_next(request)
