from typing import Any, List, Optional, Union, Literal, Dict
from pydantic import BaseModel, Field

class Interaction(BaseModel):
    """Base class for all interactions."""
    pass

class SendInteraction(Interaction):
    """Event to send to the client."""
    type: Literal["send"]
    at_ms: int = Field(..., description="Time in milliseconds from start of connection to send this message.")
    payload: Any = Field(..., description="The JSON payload to send.")

class ExpectInteraction(Interaction):
    """Event expected from the client."""
    type: Literal["expect"]
    timeout_ms: int = Field(..., description="Time in milliseconds to wait for this message relative to previous 'expect' or start.")
    match: Any = Field(..., description="Pattern to match against received message.")

class InteractionLog(BaseModel):
    """Record of an interaction that occurred."""
    timestamp: float
    direction: Literal["sent", "received"]
    payload: Any

class Script(BaseModel):
    items: List[Union[SendInteraction, ExpectInteraction]] = Field(default_factory=list)


# --- Home Assistant WebSocket API Models ---

class HAMessage(BaseModel):
    """Base Home Assistant message."""
    type: str

class HACommand(HAMessage):
    """Base message with an ID, sent by client or server resolving commands."""
    id: int

# Auth Phase
class AuthRequiredMessage(HAMessage):
    type: Literal["auth_required"] = "auth_required"
    ha_version: str = "2025.1.0"

class AuthMessage(HAMessage):
    type: Literal["auth"] = "auth"
    access_token: str

class AuthOkMessage(HAMessage):
    type: Literal["auth_ok"] = "auth_ok"
    ha_version: str = "2025.1.0"

class AuthInvalidMessage(HAMessage):
    type: Literal["auth_invalid"] = "auth_invalid"
    message: str

# Feature Enablement
class SupportedFeaturesMessage(HACommand):
    type: Literal["supported_features"] = "supported_features"
    features: Dict[str, Any]

# Command Phase (Client -> Server)
class SubscribeEventsMessage(HACommand):
    type: Literal["subscribe_events"] = "subscribe_events"
    event_type: Optional[str] = None

class UnsubscribeEventsMessage(HACommand):
    type: Literal["unsubscribe_events"] = "unsubscribe_events"
    subscription: int

class SubscribeTriggerMessage(HACommand):
    type: Literal["subscribe_trigger"] = "subscribe_trigger"
    trigger: Union[Dict[str, Any], List[Dict[str, Any]]]

class FireEventMessage(HACommand):
    type: Literal["fire_event"] = "fire_event"
    event_type: str
    event_data: Optional[Dict[str, Any]] = None

class CallServiceMessage(HACommand):
    type: Literal["call_service"] = "call_service"
    domain: str
    service: str
    service_data: Optional[Dict[str, Any]] = None
    target: Optional[Dict[str, Any]] = None
    return_response: Optional[bool] = None

class GetStatesMessage(HACommand):
    type: Literal["get_states"] = "get_states"

class GetConfigMessage(HACommand):
    type: Literal["get_config"] = "get_config"

class GetServicesMessage(HACommand):
    type: Literal["get_services"] = "get_services"

class GetPanelsMessage(HACommand):
    type: Literal["get_panels"] = "get_panels"

class PingMessage(HACommand):
    type: Literal["ping"] = "ping"

class ValidateConfigMessage(HACommand):
    type: Literal["validate_config"] = "validate_config"
    trigger: Optional[Any] = None
    condition: Optional[Any] = None
    action: Optional[Any] = None

class ExtractFromTargetMessage(HACommand):
    type: Literal["extract_from_target"] = "extract_from_target"
    target: Dict[str, Any]
    expand_group: Optional[bool] = None

class GetTriggersForTargetMessage(HACommand):
    type: Literal["get_triggers_for_target"] = "get_triggers_for_target"
    target: Dict[str, Any]
    expand_group: Optional[bool] = None

class GetConditionsForTargetMessage(HACommand):
    type: Literal["get_conditions_for_target"] = "get_conditions_for_target"
    target: Dict[str, Any]
    expand_group: Optional[bool] = None

class GetServicesForTargetMessage(HACommand):
    type: Literal["get_services_for_target"] = "get_services_for_target"
    target: Dict[str, Any]
    expand_group: Optional[bool] = None

# Command Phase (Server -> Client)
class ErrorInfo(BaseModel):
    code: str
    message: str
    translation_key: Optional[str] = None
    translation_domain: Optional[str] = None
    translation_placeholders: Optional[Dict[str, Any]] = None

class ResultMessage(HACommand):
    type: Literal["result"] = "result"
    success: bool
    result: Optional[Any] = None
    error: Optional[ErrorInfo] = None

class EventMessage(HACommand):
    type: Literal["event"] = "event"
    event: Dict[str, Any]

class PongMessage(HACommand):
    type: Literal["pong"] = "pong"
