import typer
import asyncio
from pathlib import Path
from .server import start_server

app = typer.Typer()

@app.command()
def main(
    config: Path = typer.Option(..., "-c", "--config", help="Path to the YAML scenario file."),
    host: str = typer.Option("127.0.0.1", help="Host to bind to."),
    port: int = typer.Option(8123, help="Port to bind to."),
):
    """Run the mock Home Assistant websocket server."""
    asyncio.run(start_server(host, port, config))

if __name__ == "__main__":
    app()
