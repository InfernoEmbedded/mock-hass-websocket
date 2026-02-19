import pytest
import asyncio
import json
import websockets
from pathlib import Path
from mock_hass_websocket.server import start_server

@pytest.fixture
def unused_tcp_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

@pytest.mark.asyncio
async def test_client_timeout(unused_tcp_port, tmp_path):
    # Script expects message but client doesn't send it
    content = """
    script:
      - type: expect
        timeout_ms: 200
        match: {type: "ping"}
    """
    p = tmp_path / "timeout.yaml"
    p.write_text(content)
    
    port = unused_tcp_port
    server_task = asyncio.create_task(start_server("127.0.0.1", port, p))
    await asyncio.sleep(0.5)
    
    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            # Do nothing
            await asyncio.sleep(0.5)
            # Server should have logged error or closed connection?
            # Current implementation raises TimeoutError in Engine, caught by handler, logs error.
            # Connection might remain open or closed depending on error handling.
            # We just verify we don't crash.
            pass
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

@pytest.mark.asyncio
async def test_client_sends_wrong_message(unused_tcp_port, tmp_path):
    # Script expects A, client sends B
    content = """
    script:
      - type: expect
        timeout_ms: 1000
        match: {type: "A"}
    """
    p = tmp_path / "wrong_msg.yaml"
    p.write_text(content)
    
    port = unused_tcp_port
    server_task = asyncio.create_task(start_server("127.0.0.1", port, p))
    await asyncio.sleep(0.5)
    
    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            await ws.send(json.dumps({"type": "B"}))
            # Engine logs warning and keeps waiting.
            # Client sends correct message later?
            # If client disconnects, test ends.
            await asyncio.sleep(0.1)
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

@pytest.mark.asyncio
async def test_malformed_json(unused_tcp_port, tmp_path):
    content = """
    script:
      - type: expect
        timeout_ms: 1000
        match: {type: "A"}
    """
    p = tmp_path / "malformed.yaml"
    p.write_text(content)
    
    port = unused_tcp_port
    server_task = asyncio.create_task(start_server("127.0.0.1", port, p))
    await asyncio.sleep(0.5)
    
    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            await ws.send("Not JSON")
            # Server should log error but not crash
            await asyncio.sleep(0.1)
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
