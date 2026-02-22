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
async def test_persistence(unused_tcp_port, tmp_path):
    # Script does one thing then finishes
    content = """
    script:
      - type: send
        at_ms: 0
        payload: {msg: "done"}
    """
    p = tmp_path / "persistence.yaml"
    p.write_text(content)
    
    port = unused_tcp_port
    server_task = asyncio.create_task(start_server("127.0.0.1", port, p))
    await asyncio.sleep(0.5)
    
    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}/api/websocket") as ws:
            # Receive the "done" message
            msg = await ws.recv()
            assert json.loads(msg) == {"msg": "done"}
            
            # Now the script is finished. 
            # In the old version, the server would close the connection now.
            # In the new version, it should stay open.
            
            try:
                # Wait a bit and try to receive again or just check if closed
                # recv() will raise ConnectionClosed if the server closes the socket.
                await asyncio.wait_for(ws.recv(), timeout=0.5)
            except asyncio.TimeoutError:
                # This is good! Connection stayed open but no data.
                pass
            except websockets.exceptions.ConnectionClosed:
                pytest.fail("Connection closed prematurely by server after script finished")
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
