import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from mock_hass_websocket.engine import Engine, deep_match
from mock_hass_websocket.models import Script, SendInteraction, ExpectInteraction

# deep_match tests
def test_deep_match_dict():
    assert deep_match({"a": 1, "b": 2}, {"a": 1})
    assert not deep_match({"a": 1}, {"a": 1, "b": 2})
    assert deep_match({"a": {"b": 1}}, {"a": {"b": 1}})
    assert not deep_match({"a": {"b": 2}}, {"a": {"b": 1}})

def test_deep_match_list():
    assert deep_match([1, 2], [1, 2])
    assert not deep_match([1, 2], [1])
    assert not deep_match([1], [1, 2])
    assert deep_match([{"a": 1}], [{"a": 1}])

def test_deep_match_primitives():
    assert deep_match(1, 1)
    assert not deep_match(1, 2)
    assert deep_match("foo", "foo")

# Engine tests
@pytest.mark.asyncio
async def test_engine_send(mock_websocket):
    script = Script(items=[
        SendInteraction(type="send", at_ms=10, payload={"event": "test"})
    ])
    engine = Engine(script)
    
    # Run engine
    await engine.run(mock_websocket)
    
    # Verify send called
    mock_websocket.send.assert_called_once()
    args = mock_websocket.send.call_args[0]
    assert '{"event": "test"}' in args[0]

@pytest.mark.asyncio
async def test_engine_expect_success(mock_websocket):
    script = Script(items=[
        ExpectInteraction(type="expect", timeout_ms=500, match={"type": "auth"})
    ])
    engine = Engine(script)
    
    # Reset queue just in case
    engine.packet_queue = asyncio.Queue()

    # Create a proper async iterator for mocking
    async def msg_iter():
        yield '{"type": "auth", "token": "abc"}'
        # Keep yielding or sleep to prevent StopAsyncIteration from closing the consumer loop immediately
        # forcing it to wait, although Engine handles that gracefully?
        # Engine: try... async for ... except ...
        # If iterator stops, loop finishes.
        await asyncio.sleep(0.1) 
    
    # We need to set __aiter__ on the mock. 
    # If mock_websocket is AsyncMock, we need to assign to __aiter__.return_value or side_effect.
    # But AsyncMock.__aiter__ is a function that returns the iterator.
    mock_websocket.__aiter__.side_effect = msg_iter
    
    await engine.run(mock_websocket)

@pytest.mark.asyncio
async def test_engine_expect_timeout(mock_websocket):
    script = Script(items=[
        ExpectInteraction(type="expect", timeout_ms=100, match={"type": "auth"})
    ])
    engine = Engine(script)
    
    async def msg_iter():
        await asyncio.sleep(0.5)
        yield '{}'
    
    mock_websocket.__aiter__.side_effect = msg_iter
    
    with pytest.raises(asyncio.TimeoutError):
        await engine.run(mock_websocket)

@pytest.mark.asyncio
async def test_engine_expect_ignore_mismatch(mock_websocket):
    script = Script(items=[
        ExpectInteraction(type="expect", timeout_ms=500, match={"type": "auth"})
    ])
    engine = Engine(script)
    
    async def msg_iter():
        yield '{"type": "ping"}' # Mismatch, should be ignored
        await asyncio.sleep(0.01)
        yield '{"type": "auth"}' # Match
        await asyncio.sleep(0.1)
    
    mock_websocket.__aiter__.side_effect = msg_iter
    
    await engine.run(mock_websocket)
