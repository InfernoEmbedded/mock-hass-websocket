# Mock Home Assistant WebSocket

A mock server for the [Home Assistant WebSocket API](https://developers.home-assistant.io/docs/api/websocket), designed to facilitate testing of external applications (like [AppDaemon](https://appdaemon.readthedocs.io/)) without requiring a running Home Assistant instance.

## Features

- **YAML-Driven Scenarios**: Define test scenarios (events to send, commands to expect) in simple YAML files.
- **Precise Timing**: Control when events are sent with millisecond precision.
- **Deep Matching**: Verify that clients send the expected commands with correct data.
- **Interaction Recording**: Automatically records all interactions to JSON files for regression testing.
- **Modern Asyncio**: Built on top of `websockets` 14.0+ using modern asyncio patterns.

## Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/mock-hass-websocket.git
cd mock-hass-websocket

# Install dependencies
pip install .

# Install optional test dependencies
pip install ".[test]"
```

## Usage

### Running the Server

You can run the mock server directly from the command line, providing a scenario script:

```bash
mock-hass --host 127.0.0.1 --port 8123 path/to/scenario.yaml
```

### Scenario Format

Scenarios are defined in YAML. They consist of a list of interactions:

- `send`: The server sends a message to the client at a specific time (`at_ms`).
- `expect`: The server waits for the client to send a matching message within a timeout (`timeout_ms`).

**Example `scenario.yaml`:**

```yaml
script:
  # 1. Server simulates a motion sensor turning ON
  - type: send
    at_ms: 100
    payload:
      type: event
      event: state_changed
      entity_id: binary_sensor.motion
      new_state: {state: "on", attributes: {}}

  # 2. Server expects the App to turn on the light
  - type: expect
    timeout_ms: 1000
    match:
      type: call_service
      domain: light
      service: turn_on
      service_data: {entity_id: "light.room"}
```

## Testing Your App

This project provides headers to easily test your AppDaemon apps using `pytest`.

### Async Example

See `examples/test_example_async.py` for a modern async app testing template.

### Classic Synchronous Example

See `examples/test_example_classic.py` for testing legacy synchronous apps (using threads).

### Running Examples

```bash
pytest examples/
```

## Development

Run the full test suite, including the 20 built-in scenarios:

```bash
pytest tests/
```

## License

MIT License. See [LICENSE.txt](LICENSE.txt) for details.
