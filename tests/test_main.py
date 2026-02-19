import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from typer.testing import CliRunner
from mock_hass_websocket.main import app

def test_main_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "mock Home Assistant websocket server" in result.stdout

@patch("mock_hass_websocket.main.start_server", new_callable=AsyncMock)
def test_main_cli_start(mock_start, tmp_path):
    # create dummy config
    config = tmp_path / "config.yaml"
    config.touch()
    
    runner = CliRunner()
    result = runner.invoke(app, ["--config", str(config), "--host", "0.0.0.0", "--port", "9000"])
    
    assert result.exit_code == 0
    mock_start.assert_awaited_once()
    args = mock_start.call_args[0]
    assert args[0] == "0.0.0.0"
    assert args[1] == 9000
    assert args[2] == config

def test_main_cli_missing_config():
    runner = CliRunner()
    result = runner.invoke(app, []) # Missing required --config
    assert result.exit_code != 0
