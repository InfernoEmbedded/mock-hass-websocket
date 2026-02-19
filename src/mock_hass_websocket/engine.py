import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed
from .models import Script, SendInteraction, ExpectInteraction, InteractionLog

logger = logging.getLogger(__name__)

def deep_match(received: Any, expected: Any) -> bool:
    """
    recursively check if received matches expected.
    If expected is a dict, received must be a dict and contain all keys/values from expected.
    If expected is a list, received must be a list of same length and match item by item (order matters for now).
    primitive types must match exactly.
    """
    if isinstance(expected, dict):
        if not isinstance(received, dict):
            return False
        for key, value in expected.items():
            if key not in received:
                return False
            if not deep_match(received[key], value):
                return False
        return True
    elif isinstance(expected, list):
        if not isinstance(received, list) or len(received) != len(expected):
            return False
        for r, e in zip(received, expected):
            if not deep_match(r, e):
                return False
        return True
    else:
        return received == expected

class Engine:
    def __init__(self, script: Script):
        self.script = script
        self.start_time = 0
        self.packet_queue = asyncio.Queue()
        self.history: List[InteractionLog] = []

    async def run(self, websocket: ServerConnection):
        """Run the engine for a connected client."""
        self.start_time = asyncio.get_event_loop().time()
        self.history = [] # Reset history on run
        
        # Start receiver task
        receiver_task = asyncio.create_task(self._receiver_loop(websocket))
        
        try:
            # Execute script sequentially
            for item in self.script.items:
                if isinstance(item, SendInteraction):
                    await self._handle_send(websocket, item)
                elif isinstance(item, ExpectInteraction):
                    await self._handle_expect(item)
                    
            logger.info("Script execution completed successfully.")
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            raise
        finally:
            receiver_task.cancel()

    async def _handle_send(self, websocket: ServerConnection, item: SendInteraction):
        """Handle sending an event."""
        now = asyncio.get_event_loop().time()
        target_time = self.start_time + (item.at_ms / 1000.0)
        delay = target_time - now
        
        if delay > 0:
            logger.debug(f"Waiting {delay:.3f}s to send message")
            await asyncio.sleep(delay)
        
        logger.info(f"Sending: {item.payload}")
        await websocket.send(json.dumps(item.payload))
        self.history.append(InteractionLog(
            timestamp=asyncio.get_event_loop().time(),
            direction="sent",
            payload=item.payload
        ))

    async def _handle_expect(self, item: ExpectInteraction):
        """Handle expecting an event."""
        logger.info(f"Expecting: {item.match} within {item.timeout_ms}ms (relative to now)")
        
        timeout = item.timeout_ms / 1000.0
        start_wait = asyncio.get_event_loop().time()
        
        while True:
            # Calculate remaining time
            elapsed = asyncio.get_event_loop().time() - start_wait
            remaining = timeout - elapsed
            
            if remaining <= 0:
                raise asyncio.TimeoutError(f"Expected {item.match} but timed out after {item.timeout_ms}ms")
            
            try:
                # Wait for next message from queue
                message = await asyncio.wait_for(self.packet_queue.get(), timeout=remaining)
                
                # Check if it matches
                if deep_match(message, item.match):
                    logger.info(f"Matched expectation: {message}")
                    return
                else:
                    logger.warning(f"Received message {message} did not match expected {item.match}, skipping...")
                    pass
                    
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for expectation: {item.match}")
                raise

    async def _receiver_loop(self, websocket: ServerConnection):
        """Loop to receive messages and put them in queue."""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Received: {data}")
                    self.history.append(InteractionLog(
                        timestamp=asyncio.get_event_loop().time(),
                        direction="received",
                        payload=data
                    ))
                    await self.packet_queue.put(data)
                except json.JSONDecodeError:
                    logger.error(f"Received invalid JSON: {message}")
        except asyncio.CancelledError:
            pass
        except ConnectionClosed:
            logger.info("Connection closed in receiver loop")
