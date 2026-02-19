from typing import Any, List, Optional, Union, Literal
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
