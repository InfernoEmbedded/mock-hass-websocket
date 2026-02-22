import pytest
import asyncio
from mock_hass_websocket.engine import Engine
from mock_hass_websocket.models import Script, ExpectInteraction

@pytest.mark.asyncio
async def test_engine_buffering():
    # Arrange: Script expects messages in order: A, B
    script = Script(items=[
        ExpectInteraction(type="expect", timeout_ms=500, match={"msg": "A"}),
        ExpectInteraction(type="expect", timeout_ms=500, match={"msg": "B"}),
    ])
    engine = Engine(script)
    
    # Act: Send B then A into the packet queue
    await engine.packet_queue.put({"msg": "B"})
    await engine.packet_queue.put({"msg": "A"})
    
    # Assert: Handle expectations
    # 1. Expect A: should see B, buffer it, then see A and match
    await engine._handle_expect(script.items[0])
    assert len(engine._skipped_packets) == 1
    assert engine._skipped_packets[0] == {"msg": "B"}
    
    # 2. Expect B: should find B in buffer immediately
    await engine._handle_expect(script.items[1])
    assert len(engine._skipped_packets) == 0

@pytest.mark.asyncio
async def test_engine_buffering_multiple():
    script = Script(items=[
        ExpectInteraction(type="expect", timeout_ms=500, match={"msg": "1"}),
        ExpectInteraction(type="expect", timeout_ms=500, match={"msg": "2"}),
        ExpectInteraction(type="expect", timeout_ms=500, match={"msg": "3"}),
    ])
    engine = Engine(script)
    
    # Send 3, 2, 1
    await engine.packet_queue.put({"msg": "3"})
    await engine.packet_queue.put({"msg": "2"})
    await engine.packet_queue.put({"msg": "1"})
    
    # Expect 1 -> 3, 2 buffered. 1 matched.
    await engine._handle_expect(script.items[0])
    assert len(engine._skipped_packets) == 2
    
    # Expect 2 -> 2 found in buffer. 3 remains.
    await engine._handle_expect(script.items[1])
    assert len(engine._skipped_packets) == 1
    assert engine._skipped_packets[0] == {"msg": "3"}
    
    # Expect 3 -> 3 found in buffer.
    await engine._handle_expect(script.items[2])
    assert len(engine._skipped_packets) == 0
