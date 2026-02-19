import pytest
from pydantic import ValidationError
from mock_hass_websocket.models import SendInteraction, ExpectInteraction, Script

def test_send_interaction_valid():
    interaction = SendInteraction(type="send", at_ms=100, payload={"foo": "bar"})
    assert interaction.type == "send"
    assert interaction.at_ms == 100
    assert interaction.payload == {"foo": "bar"}

def test_send_interaction_invalid_type():
    with pytest.raises(ValidationError):
        SendInteraction(type="invalid", at_ms=100, payload={})

def test_send_interaction_missing_fields():
    with pytest.raises(ValidationError):
        SendInteraction(type="send")

def test_expect_interaction_valid():
    interaction = ExpectInteraction(type="expect", timeout_ms=500, match={"state": "on"})
    assert interaction.type == "expect"
    assert interaction.timeout_ms == 500
    assert interaction.match == {"state": "on"}

def test_expect_interaction_negative_timeout():
    # Pydantic doesn't strictly enforce >0 unless constrained, checking implementation
    # But usually time should be non-negative. 
    # Let's see if our model allows it. It probably does since we didn't add constrains.
    # This test documents current behavior.
    interaction = ExpectInteraction(type="expect", timeout_ms=-10, match={})
    assert interaction.timeout_ms == -10

def test_script_valid():
    data = Script(items=[
        SendInteraction(type="send", at_ms=0, payload="hello"),
        ExpectInteraction(type="expect", timeout_ms=100, match="world")
    ])
    assert len(data.items) == 2
    assert isinstance(data.items[0], SendInteraction)
    assert isinstance(data.items[1], ExpectInteraction)

def test_script_empty():
    script = Script(items=[])
    assert script.items == []
