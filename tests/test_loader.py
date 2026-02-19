import pytest
import yaml
from pathlib import Path
from mock_hass_websocket.loader import load_script
from mock_hass_websocket.models import SendInteraction, ExpectInteraction

def test_load_script_valid(tmp_path):
    script_content = """
    script:
      - type: send
        at_ms: 100
        payload: {event: hello}
      - type: expect
        timeout_ms: 500
        match: {event: world}
    """
    p = tmp_path / "scenario.yaml"
    p.write_text(script_content)

    script = load_script(p)
    assert len(script.items) == 2
    assert isinstance(script.items[0], SendInteraction)
    assert script.items[0].at_ms == 100
    assert isinstance(script.items[1], ExpectInteraction)
    assert script.items[1].timeout_ms == 500

def test_load_script_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_script(Path("non_existent_file.yaml"))

def test_load_script_invalid_yaml(tmp_path):
    p = tmp_path / "invalid.yaml"
    p.write_text("script: [ unclosed list")
    
    with pytest.raises(yaml.YAMLError):
        load_script(p)

def test_load_script_unknown_interaction_type(tmp_path):
    script_content = """
    script:
      - type: unknown_type
        some_field: 123
    """
    p = tmp_path / "bad_type.yaml"
    p.write_text(script_content)

    with pytest.raises(ValueError, match="Unknown interaction type"):
        load_script(p)

def test_load_script_missing_script_key(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("foo: bar")
    
    # helper returns empty script if key missing
    script = load_script(p)
    assert script.items == []
