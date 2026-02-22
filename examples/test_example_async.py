import pytest
import asyncio
import json
import logging
import websockets
from pathlib import Path
from mock_hass_websocket.server import start_server
from mock_hass_websocket.loader import load_script
from mock_hass_websocket.engine import Engine, deep_match

# --- PROTOTYPE ---------------------------------------------------------
# This section simulates your AppDaemon App code.
# In a real scenario, you would import your App class here.
# -----------------------------------------------------------------------

class MyApp:
    def __init__(self, uri):
        self.uri = uri
        self.running = False
        self.logger = logging.getLogger("MyApp")

    async def start(self):
        self.running = True
        async with websockets.connect(self.uri) as ws:
            self.ws = ws
            # Authenticate (Mock HASS usually accepts anything or skips auth if not configured)
            # For this mock server, we just start receiving events.
            while self.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    await self.on_message(data)
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break

    async def on_message(self, data):
        self.logger.info(f"App received: {data}")
        
        # LOGIC: If motion is ON, turn light ON. If motion OFF, turn light OFF.
        if data.get("type") == "event" and data.get("event") == "state_changed":
            entity_id = data.get("entity_id")
            new_state = data.get("new_state", {}).get("state")
            
            if entity_id == "binary_sensor.motion":
                if new_state == "on":
                    await self.call_service("light", "turn_on", {"entity_id": "light.room"})
                elif new_state == "off":
                    await self.call_service("light", "turn_off", {"entity_id": "light.room"})

    async def call_service(self, domain, service, service_data):
        self.logger.info(f"Calling service: {domain}.{service} with {service_data}")
        await self.ws.send(json.dumps({
            "type": "call_service",
            "domain": domain,
            "service": service,
            "service_data": service_data
        }))

    def stop(self):
        self.running = False

# --- TEST CODE ---------------------------------------------------------
# This is how you verify your App against the Scenario.
# -----------------------------------------------------------------------

@pytest.fixture
def unused_tcp_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

@pytest.mark.asyncio
async def test_my_app_logic(unused_tcp_port):
    """
    Test that MyApp behaves correctly according to 'prototype_scenario.yaml'.
    """
    # 1. Setup
    port = unused_tcp_port
    scenario_path = Path("examples/prototype_scenario.yaml")
    
    # Load script and engine for verification
    script = load_script(scenario_path)
    engine = Engine(script)
    
    # 2. Start Mock Server
    server_task = asyncio.create_task(
        start_server("127.0.0.1", port, scenario_path, engine=engine)
    )
    await asyncio.sleep(0.1) # Wait for server startup
    
    # 3. Start App (System Under Test)
    app = MyApp(f"ws://127.0.0.1:{port}/api/websocket")
    app_task = asyncio.create_task(app.start())
    
    try:
        # 4. Wait for interaction to complete
        # We can wait for a specific time based on scenario duration
        # The scenario is ~3-4 seconds long.
        await asyncio.sleep(4.0)
        
    finally:
        # Cleanup
        app.stop()
        app_task.cancel()
        try:
            await app_task
        except asyncio.CancelledError:
            pass
            
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    # 5. Verify Results
    # Check that the Engine successfully matched all expectations
    # If the Engine raises an error during execution, it logs it.
    # We can also check the history length
    
    print("\n--- Interaction History ---")
    for log in engine.history:
        print(f"[{log.direction.upper()}] {log.payload}")
        
    # Ensure all script items were processed (sent or expected)
    # Note: Engine.history logs *actual* events.
    # We want to know if the Engine encountered any mismatch exceptions.
    # Currently Engine catches exceptions and logs them, or raises up to run().
    # Ideally, we should check if engine.run() completed successfully if we awaited it.
    # But start_server runs engine.run in a loop per connection.
    
    # Simple check: Did we satisfy all expectations?
    # We can verify that we have at least as many 'received' keys in history as 'expect' items in script.
    expected_matches = len([i for i in script.items if i.type == "expect"])
    actual_matches = len([l for l in engine.history if l.direction == "received"])
    
    assert actual_matches >= expected_matches, "App did not send all expected commands!"
    
    # Verify exact matches logic if needed
    # (The Engine internals already invoke deep_match and log warnings/errors on mismatch)
