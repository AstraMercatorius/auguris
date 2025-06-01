import json
from fastapi.testclient import TestClient
from src.webserver import get_webserver, app
import uvicorn

client = TestClient(app)

def test_get_webserver_returns_server_with_expected_config():
    server = get_webserver()
    assert isinstance(server, uvicorn.Server)
    config = server.config
    assert config.app == app
    assert config.host == "0.0.0.0"
    assert config.port == 5500
    assert config.log_level == "info"
    assert config.loop == "asyncio"

def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert '{"status": "ok"}' in json.dumps(response.json())
