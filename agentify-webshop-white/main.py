"""CLI entrypoint for Agentified WebShop, compatible with AgentBeats controller."""

import asyncio
import os
import typer

from src.green_agent.agent import start_green_agent
from src.white_agent.agent import start_white_agent
from src.launcher import launch_evaluation


app = typer.Typer(help="Agentified WebShop - controller-friendly entrypoint")


def _common_net_config():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_PORT", "8000"))
    return host, port


@app.command()
def green():
    """Start the green agent (assessment manager)."""
    host, port = _common_net_config()
    start_green_agent(host=host, port=port)


@app.command()
def white():
    """Start the white agent (target being tested)."""
    host, port = _common_net_config()
    start_white_agent(host=host, port=port)


@app.command()
def run():
    """Start an agent based on ROLE env: green|white."""
    role = os.getenv("ROLE", "").lower()
    if role not in ("green", "white"):
        raise ValueError("ROLE must be set to 'green' or 'white'")
    if role == "green":
        green()
    else:
        white()


@app.command()
def launch():
    """Launch local evaluation (starts both agents) -- for local testing only."""
    asyncio.run(launch_evaluation())


if __name__ == "__main__":
    app()
