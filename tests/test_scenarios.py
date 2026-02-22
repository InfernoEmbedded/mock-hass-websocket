import pytest
import asyncio
import json
import websockets
from pathlib import Path
from mock_hass_websocket.loader import load_script
from mock_hass_websocket.server import start_server
from mock_hass_websocket.models import SendInteraction, ExpectInteraction

SCENARIOS_DIR = Path("scenarios")
SCENARIO_FILES = sorted(list(SCENARIOS_DIR.glob("*.yaml")))

# Helper to find an unused port
@pytest.fixture
def unused_tcp_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

from mock_hass_websocket.engine import Engine, deep_match

async def run_complementary_client(ws, script):
    """
    Drive the client based on the server's script.
    """
    for item in script.items:
        if isinstance(item, SendInteraction):
            # Server sends, we receive
            # Use a generous timeout; some scenarios wait 5s
            msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(msg)
        elif isinstance(item, ExpectInteraction):
            # Server expects, we send
            payload = item.match
            await ws.send(json.dumps(payload))
            await asyncio.sleep(0.1)

def verify_history(engine: Engine, script, scenario_file: Path):
    """Verify engine history and record/compare with file."""
    # 1. basic verification
    assert len(engine.history) >= len(script.items)
    
    # 2. Normalize and serialize
    # We want to ignore exact timestamps but maybe keep relative ordering or time deltas if important?
    # User said "ignoring variable data like timestamps".
    # So we'll strip timestamps for comparison.
    
    actual_records = []
    for log in engine.history:
        record = log.model_dump()
        # Remove variable fields
        del record["timestamp"]
        actual_records.append(record)
    
    # Define recording path
    # e.g. scenarios/recordings/1_thermostat_cool.json
    recording_path = SCENARIOS_DIR / "recordings" / (scenario_file.stem + ".json")
    
    if recording_path.exists():
        # Compare
        with open(recording_path, "r") as f:
            expected_records = json.load(f)
        
        # We might have more actual records than expected if we log pings/etc?
        # But for strictly controlled tests, they should match exactly or be a superset?
        # Let's assert exact match for now as our scenarios are deterministic.
        
        # Deep diff or simple equality?
        # Simple equality of list of dicts should work if deterministic.
        assert actual_records == expected_records, f"History mismatch for {scenario_file.name}"
    else:
        # Record (First run)
        # We might want to warn or just save.
        # Impling "auto-generate on missing".
        with open(recording_path, "w") as f:
            json.dump(actual_records, f, indent=2)
        # Pass the test this time, but maybe warn?
        import warnings
        warnings.warn(f"Generated new recording for {scenario_file.name}")

@pytest.mark.asyncio
@pytest.mark.parametrize("scenario_file", SCENARIO_FILES)
async def test_scenario_end_to_end(unused_tcp_port, scenario_file):
    port = unused_tcp_port
    host = "127.0.0.1"
    
    # Load script and create engine manually to access it later
    script = load_script(scenario_file)
    engine = Engine(script)
    
    # Start server with injected engine
    server_task = asyncio.create_task(start_server(host, port, scenario_file, engine=engine))
    await asyncio.sleep(0.5) # Wait for startup
    
    try:
        async with websockets.connect(f"ws://{host}:{port}/api/websocket") as ws:
            await run_complementary_client(ws, script)
        
        # Verify history
        verify_history(engine, script, scenario_file)
            
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
