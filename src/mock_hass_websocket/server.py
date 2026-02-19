import asyncio
import logging
import signal
from typing import Optional
from websockets.asyncio.server import serve, ServerConnection
from .engine import Engine
from .loader import load_script
from pathlib import Path

logger = logging.getLogger(__name__)

async def handler(websocket: ServerConnection, engine: Engine):
    """Handle a websocket connection."""
    logger.info(f"Client connected: {websocket.remote_address}")
    try:
        await engine.run(websocket)
    except Exception as e:
        # ConnectionClosed is handled by engine or raises here?
        # In new API, potential exceptions might differ slightly but usually 
        # ConnectionClosedOK/Error are raised.
        logger.error(f"Error during execution: {e}")
    finally:
        logger.info("Handler finished")

async def start_server(host: str, port: int, script_path: Path, engine: Optional[Engine] = None):
    """Start the websocket server."""
    logging.basicConfig(level=logging.INFO)
    
    if engine is None:
        logger.info(f"Loading script from {script_path}")
        script = load_script(script_path)
        engine = Engine(script)

    # Use bound handler to pass engine
    async def bound_handler(ws: ServerConnection):
        await handler(ws, engine)

    async with serve(bound_handler, host, port) as server:
        logger.info(f"Server started on ws://{host}:{port}")
        stop = asyncio.Future()
        def terminate():
            if not stop.done():
                stop.set_result(None)
        
        loop = asyncio.get_running_loop()
        # Add signal handlers if possible (might error if not in main thread)
        try:
            loop.add_signal_handler(signal.SIGINT, terminate)
            loop.add_signal_handler(signal.SIGTERM, terminate)
        except NotImplementedError:
            # For Windows or non-main threads
            pass
        
        await stop
