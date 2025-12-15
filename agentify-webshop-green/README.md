# Agentify WebShop – AgentBeats Integration Notes

## Controller-first usage (AgentBeats)
- Start via AgentBeats controller (Procfile):  
  `web: agentbeats run_ctrl`
- Entry command for the controller: `./run.sh` (runs `python main.py run`).
- Environment variables consumed:  
  - `ROLE`: `green` or `white` (required)  
  - `HOST`: default `0.0.0.0`  
  - `AGENT_PORT`: default `8000`  
  - `AGENT_URL`: injected by controller; advertised in the agent card  
- Each agent binds to `HOST`/`AGENT_PORT` and sets its card URL from `AGENT_URL`.

## Local dual-agent testing (no controller)
- For local end-to-end evaluation (spawns both agents):  
  `python -m src.launcher`  
  This is for local testing only; **do not** use with the controller.

## Regenerating dependency files
- requirements.txt from pyproject:  
  `uv export --no-hashes --format=requirements-txt > requirements.txt`  
  (or `pip freeze > requirements.txt` if not using uv)
- uv.lock from pyproject:  
  `uv lock`

## Sanity checks with the controller
1) Run green under controller:  
   `ROLE=green HOST=0.0.0.0 AGENT_PORT=9001 agentbeats run_ctrl`
2) In a second terminal, run white:  
   `ROLE=white HOST=0.0.0.0 AGENT_PORT=9002 agentbeats run_ctrl`
3) Verify agent card via controller proxy: fetch `.well-known/agent-card.json` from the controller URL.  
4) Send a test message through the controller proxy (e.g., using the AgentBeats UI or a2a client) to confirm round-trip.
