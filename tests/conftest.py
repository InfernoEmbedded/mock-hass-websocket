import pytest
import asyncio
from unittest.mock import AsyncMock
from websockets.asyncio.server import ServerConnection

@pytest.fixture
def mock_websocket():
    ws = AsyncMock(spec=ServerConnection)
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.remote_address = ("127.0.0.1", 12345)
    return ws

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
