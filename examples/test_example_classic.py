import pytest
import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from websockets.sync.client import connect  # Synchronous client
from mock_hass_websocket.server import start_server
from mock_hass_websocket.loader import load_script
from mock_hass_websocket.engine import Engine

# --- CLASSIC PROTOTYPE -------------------------------------------------
# This simulates a "Classic" synchronous AppDaemon App.
# -----------------------------------------------------------------------

class ClassicApp:
    def __init__(self, uri):
        self.uri = uri
        self.running = False
        self.logger = logging.getLogger("ClassicApp")
        self.ws = None

    def start(self):
        """Start the app in a blocking manner (or thread)."""
        self.running = True
        try:
            # Using synchronous websocket client
            with connect(self.uri) as ws:
                self.ws = ws
                while self.running:
                    try:
                        # Blocking recv with timeout
                        msg = ws.recv(timeout=1.0)
                        data = json.loads(msg)
                        self.on_message(data)
                    except TimeoutError:
                        continue
                    except Exception as e:
                        if self.running:
                            self.logger.error(f"Error: {e}")
                        break
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")

    def on_message(self, data):
        self.logger.info(f"App received: {data}")
        
        # LOGIC: Synchronous processing
        if data.get("type") == "event" and data.get("event") == "state_changed":
            entity_id = data.get("entity_id")
            new_state = data.get("new_state", {}).get("state")
            
            if entity_id == "binary_sensor.motion":
                if new_state == "on":
                    self.call_service("light", "turn_on", {"entity_id": "light.room"})
                elif new_state == "off":
                    self.call_service("light", "turn_off", {"entity_id": "light.room"})

    def call_service(self, domain, service, service_data):
        self.logger.info(f"Calling service: {domain}.{service} with {service_data}")
        # Blocking send
        self.ws.send(json.dumps({
            "type": "call_service",
            "domain": domain,
            "service": service,
            "service_data": service_data
        }))

    def stop(self):
        self.running = False
        # If we are in recv(), we might need to close socket to unblock, 
        # but the loop checks running flag after timeout.

# --- TEST CODE ---------------------------------------------------------

@pytest.fixture
def unused_tcp_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

@pytest.mark.asyncio
async def test_classic_app_logic(unused_tcp_port):
    """
    Test a synchronous app running in a separate thread against the async mock server.
    """
    # 1. Setup
    port = unused_tcp_port
    scenario_path = Path("examples/prototype_scenario.yaml")
    
    script = load_script(scenario_path)
    engine = Engine(script)
    
    # 2. Start Mock Server (Async)
    server_task = asyncio.create_task(
        start_server("127.0.0.1", port, scenario_path, engine=engine)
    )
    await asyncio.sleep(0.5) # Wait for server startup
    
    # 3. Start Classic App (In a Thread because it blocks)
    app = ClassicApp(f"ws://127.0.0.1:{port}")
    
    app_thread = threading.Thread(target=app.start)
    app_thread.start()
    
    try:
        # 4. Wait for interaction to complete
        await asyncio.sleep(4.0)
        
    finally:
        # Cleanup
        app.stop()
        app_thread.join(timeout=1.0)
            
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    # 5. Verify Results
    print("\n--- Interaction History ---")
    for log in engine.history:
        print(f"[{log.direction.upper()}] {log.payload}")
        
    expected_matches = len([i for i in script.items if i.type == "expect"])
    actual_matches = len([l for l in engine.history if l.direction == "received"])
    
    assert actual_matches >= expected_matches, "App did not send all expected commands!"
