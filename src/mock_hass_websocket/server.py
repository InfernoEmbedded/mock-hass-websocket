import asyncio
import logging
import signal
from typing import Optional
from websockets.asyncio.server import serve, ServerConnection
from .engine import Engine
from .loader import load_script
from pathlib import Path

logger = logging.getLogger(__name__)

from aiohttp import web

class WebsocketAdapter:
    """Adapts aiohttp WebSocketResponse to the websockets ServerConnection API that Engine expects."""
    def __init__(self, ws, request):
        self.ws = ws
        # Mock remote address
        self.remote_address = request.remote
        
    async def send(self, data):
        await self.ws.send_str(data)
        
    async def __aiter__(self):
        import aiohttp
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                yield msg.data
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break

async def start_server(host: str, port: int, script_path: Path, engine: Optional[Engine] = None):
    """Start the websocket server using aiohttp to support REST calls."""
    logging.basicConfig(level=logging.INFO)
    
    if engine is None:
        logger.info(f"Loading script from {script_path}")
        script = load_script(script_path)
        engine = Engine(script)

    async def websocket_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        adapter = WebsocketAdapter(ws, request)
        logger.info(f"Client connected: {adapter.remote_address}")
        try:
            await engine.run(adapter)
        except Exception as e:
            logger.error(f"Error during execution: {e}")
        finally:
            logger.info("Handler finished")
        return ws

    async def rest_handler(request):
        # Just return HTTP 200 for any api call AppDaemon makes
        # Must read the body to avoid TCP RST when the client sends a payload
        await request.read()
        return web.json_response({})

    app = web.Application()
    app.router.add_get('/api/websocket', websocket_handler)
    # Catch all POST requests to /api/states/*
    app.router.add_post('/api/states/{tail:.*}', rest_handler)
    app.router.add_get('/api/states/{tail:.*}', rest_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    
    logger.info(f"Server started on http://{host}:{port}")
    await site.start()
    
    stop = asyncio.Future()
    def terminate():
        if not stop.done():
            stop.set_result(None)
    
    loop = asyncio.get_running_loop()
    try:
        loop.add_signal_handler(signal.SIGINT, terminate)
        loop.add_signal_handler(signal.SIGTERM, terminate)
    except NotImplementedError:
        pass
    
    await stop
    await runner.cleanup()
