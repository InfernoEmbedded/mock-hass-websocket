import yaml
from pathlib import Path
from .models import Script, SendInteraction, ExpectInteraction

def load_script(path: Path) -> Script:
    """Load script from a YAML file."""
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    
    interactions = []
    for item in data.get("script", []):
        if item.get("type") == "send":
            interactions.append(SendInteraction(**item))
        elif item.get("type") == "expect":
            interactions.append(ExpectInteraction(**item))
        else:
            raise ValueError(f"Unknown interaction type: {item.get('type')}")
            
    return Script(items=interactions)
