import pytest
import asyncio
import json
import websockets
from pathlib import Path
from mock_hass_websocket.server import start_server

@pytest.fixture
def unused_tcp_port():
    """Find an unused TCP port."""
    # pytest-asyncio might provide this, but let's be safe
    # actually pytest-asyncio doesn't strictly provide unused_tcp_port fixture by default in all versions
    # but let's try to bind to port 0 and see what we get, or just use a random high port
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

@pytest.mark.asyncio
async def test_server_end_to_end(unused_tcp_port, tmp_path):
    # Create a simple script
    script_content = """
    script:
      - type: send
        at_ms: 10
        payload: {type: auth_required}
      - type: expect
        timeout_ms: 1000
        match: {type: auth, access_token: "123"}
      - type: send
        at_ms: 20
        payload: {type: auth_ok}
    """
    script_path = tmp_path / "scenario.yaml"
    script_path.write_text(script_content)
    
    port = unused_tcp_port
    host = "127.0.0.1"
    
    # Start server in background task
    # start_server runs until stopped. We need a way to stop it.
    # The current implementation of start_server awaits a future 'stop'.
    # We can't easily cancel it unless we change start_server to return the server object or accept a stop signal.
    # However, start_server handles SIGINT/SIGTERM.
    # For testing, we might want to run the server logic directly or modify start_server to be more testable.
    
    # Let's import the handler and engine and test those integrated, 
    # OR run start_server and kill it?
    
    # Better: run start_server as a task, then cancel it.
    
    server_task = asyncio.create_task(start_server(host, port, script_path))
    
    # Wait for server to start (a bit hacky, but simple)
    await asyncio.sleep(0.5)
    
    try:
        async with websockets.connect(f"ws://{host}:{port}/api/websocket") as ws:
            # 1. Expect auth_required
            msg = await ws.recv()
            data = json.loads(msg)
            assert data == {"type": "auth_required"}
            
            # 2. Send auth
            await ws.send(json.dumps({"type": "auth", "access_token": "123"}))
            
            # 3. Expect auth_ok
            msg = await ws.recv()
            data = json.loads(msg)
            assert data == {"type": "auth_ok"}
            
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
