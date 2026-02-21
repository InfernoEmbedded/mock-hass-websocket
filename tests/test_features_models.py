import pytest
from pydantic import ValidationError
from mock_hass_websocket.models import (
    AuthRequiredMessage, AuthMessage, AuthOkMessage, AuthInvalidMessage,
    SupportedFeaturesMessage, SubscribeEventsMessage, UnsubscribeEventsMessage,
    SubscribeTriggerMessage, FireEventMessage, CallServiceMessage,
    GetStatesMessage, GetConfigMessage, GetServicesMessage, GetPanelsMessage,
    PingMessage, ValidateConfigMessage, ExtractFromTargetMessage,
    GetTriggersForTargetMessage, GetConditionsForTargetMessage,
    GetServicesForTargetMessage, ResultMessage, EventMessage, PongMessage,
    ErrorInfo
)

# Auth Phase Tests
def test_auth_required():
    msg = AuthRequiredMessage()
    assert msg.type == "auth_required"
    assert "ha_version" in msg.model_dump()

def test_auth():
    msg = AuthMessage(access_token="abc")
    assert msg.type == "auth"
    assert msg.access_token == "abc"

def test_auth_ok():
    msg = AuthOkMessage()
    assert msg.type == "auth_ok"

def test_auth_invalid():
    msg = AuthInvalidMessage(message="Invalid token")
    assert msg.type == "auth_invalid"
    assert msg.message == "Invalid token"

# Feature Enablement
def test_supported_features():
    msg = SupportedFeaturesMessage(id=1, features={"coalesce_messages": 1})
    assert msg.id == 1
    assert msg.type == "supported_features"
    assert msg.features["coalesce_messages"] == 1

# Command Phase
def test_subscribe_events():
    msg = SubscribeEventsMessage(id=2, event_type="state_changed")
    assert msg.type == "subscribe_events"
    assert msg.event_type == "state_changed"

    msg_all = SubscribeEventsMessage(id=3)
    assert msg_all.event_type is None

def test_unsubscribe_events():
    msg = UnsubscribeEventsMessage(id=4, subscription=2)
    assert msg.type == "unsubscribe_events"
    assert msg.subscription == 2

def test_subscribe_trigger():
    msg = SubscribeTriggerMessage(id=5, trigger={"platform": "state", "entity_id": "sensor.test"})
    assert msg.type == "subscribe_trigger"
    assert msg.trigger["platform"] == "state"

    msg_list = SubscribeTriggerMessage(id=6, trigger=[{"platform": "time", "at": "10:00:00"}])
    assert isinstance(msg_list.trigger, list)

def test_fire_event():
    msg = FireEventMessage(id=7, event_type="custom_event", event_data={"some": "data"})
    assert msg.type == "fire_event"
    assert msg.event_type == "custom_event"
    assert msg.event_data == {"some": "data"}

def test_call_service():
    msg = CallServiceMessage(
        id=8,
        domain="light",
        service="turn_on",
        service_data={"brightness": 255},
        target={"entity_id": "light.bedroom"}
    )
    assert msg.type == "call_service"
    assert msg.domain == "light"
    assert msg.service == "turn_on"

# Fetching
def test_get_states():
    msg = GetStatesMessage(id=9)
    assert msg.type == "get_states"

def test_get_config():
    msg = GetConfigMessage(id=10)
    assert msg.type == "get_config"

def test_get_services():
    msg = GetServicesMessage(id=11)
    assert msg.type == "get_services"

def test_get_panels():
    msg = GetPanelsMessage(id=12)
    assert msg.type == "get_panels"

def test_ping():
    msg = PingMessage(id=13)
    assert msg.type == "ping"

def test_validate_config():
    msg = ValidateConfigMessage(id=14, trigger={"platform": "state"}, condition={"condition": "or"})
    assert msg.type == "validate_config"

def test_target_commands():
    msg1 = ExtractFromTargetMessage(id=15, target={"entity_id": "group.all"}, expand_group=True)
    assert msg1.type == "extract_from_target"

    msg2 = GetTriggersForTargetMessage(id=16, target={"device_id": "xyz"})
    assert msg2.type == "get_triggers_for_target"

# Server -> Client Responses
def test_result_success():
    msg = ResultMessage(id=17, success=True, result={"context": {"id": "123"}})
    assert msg.type == "result"
    assert msg.success is True

def test_result_error():
    error_info = ErrorInfo(
        code="invalid_format",
        message="Message incorrectly formatted",
        translation_key="bad_format",
        translation_domain="test"
    )
    msg = ResultMessage(id=18, success=False, error=error_info)
    assert msg.type == "result"
    assert msg.success is False
    assert msg.error.code == "invalid_format"

def test_event():
    msg = EventMessage(id=19, event={"data": {"new_state": "on"}})
    assert msg.type == "event"
    assert msg.event["data"]["new_state"] == "on"

def test_pong():
    msg = PongMessage(id=20)
    assert msg.type == "pong"
