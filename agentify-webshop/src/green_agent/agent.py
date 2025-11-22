"""Green agent implementation for WebShop."""

import uvicorn
try:
    import tomllib
except ImportError:
    import tomli as tomllib
import dotenv
import json
import time
import sys
import os

# Ensure webshop benchmark is in path so we can import its modules
# Adjust this path if the user runs from a different location
WEBSHOP_PATH = os.path.abspath("../webshop-benchmark")
if WEBSHOP_PATH not in sys.path:
    sys.path.append(WEBSHOP_PATH)

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, SendMessageSuccessResponse, Message
from a2a.utils import new_agent_text_message, get_text_parts
from src.my_util import parse_tags, send_message

# Import WebShop environment
try:
    from web_agent_site.envs import WebAgentTextEnv
except ImportError as e:
    print(f"Warning: Could not import WebAgentTextEnv. Error: {e}")
    # Also try printing sys.path
    print(f"sys.path: {sys.path}")

dotenv.load_dotenv()

def load_agent_card_toml(agent_name):
    current_dir = __file__.rsplit("/", 1)[0]
    with open(f"{current_dir}/{agent_name}.toml", "rb") as f:
        return tomllib.load(f)

async def ask_agent_to_solve(white_agent_url, env, max_num_steps=50):
    total_cost = 0.0
    # Reset env to get initial observation and instruction
    obs, _ = env.reset()
    instruction = env.instruction_text
    
    # Construct initial task description for the white agent
    # We frame the WebShop task as a tool-use problem or simple action generation problem
    task_description = f"""
You are an agent shopping on a website.
Your Goal: {instruction}

Available Actions:
1. search[keywords] - Search for products
2. click[option] - Click on a link, button, or option (e.g., click[search], click[back to search], click[b000...])

Here is the current page observation:
{obs}

Please respond in JSON format wrapped in <json> tags:
<json>
{{
  "action": "search[...]" or "click[...]"
}}
</json>
"""

    next_green_message = task_description
    context_id = None
    reward = 0.0
    done = False
    history = []

    for step in range(max_num_steps):
        print(f"@@@ Green agent: Step {step+1}. Sending observation to white agent...")
        
        white_agent_response = await send_message(
            white_agent_url, next_green_message, context_id=context_id
        )
        
        res_root = white_agent_response.root
        assert isinstance(res_root, SendMessageSuccessResponse)
        res_result = res_root.result
        
        if context_id is None:
            context_id = res_result.context_id
        
        text_parts = get_text_parts(res_result.parts)
        white_text = text_parts[0]
        print(f"@@@ White agent response:\n{white_text}")
        
        # Parse action
        try:
            tags = parse_tags(white_text)
            if "json" in tags:
                action_data = json.loads(tags["json"])
                action = action_data.get("action", "")
            else:
                # Fallback: try to interpret raw text if simple
                action = white_text.strip()
                
            print(f"@@@ Executing Action: {action}")
            
            # Execute in WebShop
            obs, reward, done, info = env.step(action)
            
            history.append((action, reward))
            
            if done:
                print(f"@@@ Episode Done. Reward: {reward}")
                break
                
            # Prepare next message
            next_green_message = f"""
Action executed: {action}
Current Page Observation:
{obs}

Please provide your next action in <json> tags.
"""
        except Exception as e:
            print(f"@@@ Error parsing or executing action: {e}")
            next_green_message = f"Error: {str(e)}. Please ensure you output valid JSON with an 'action' field."

    return {
        "success": reward == 1.0,
        "reward": reward,
        "steps": step + 1,
        "history": history
    }

class WebShopGreenAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print("Green agent: Received a task, parsing...")
        user_input = context.get_user_input()
        tags = parse_tags(user_input)
        white_agent_url = tags.get("white_agent_url")
        env_config_str = tags.get("env_config")
        
        if not white_agent_url or not env_config_str:
            await event_queue.enqueue_event(
                new_agent_text_message("Error: Missing <white_agent_url> or <env_config> tags.")
            )
            return

        env_config = json.loads(env_config_str)
        
        print("Green agent: Setting up WebShop environment...")
        # Initialize WebShop Env
        # Note: We rely on the standard WebShop setup. 
        # ideally we pass the specific session or goal index if we want deterministic eval
        env = WebAgentTextEnv(
            observation_mode="text",
            num_products=env_config.get("num_products", 1000),
            human_goals=env_config.get("human_goals", True)
        )
        
        print("Green agent: Starting evaluation...")
        timestamp_started = time.time()
        
        metrics = await ask_agent_to_solve(white_agent_url, env)
        
        metrics["time_used"] = time.time() - timestamp_started
        result_emoji = "✅" if metrics["success"] else "❌"
        
        print("Green agent: Evaluation complete.")
        await event_queue.enqueue_event(
            new_agent_text_message(
                f"Finished. White agent success: {result_emoji}\nMetrics: {json.dumps(metrics, indent=2)}\n"
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError

def start_green_agent(agent_name="webshop_green_agent", host="localhost", port=9001):
    print(f"Starting green agent on {host}:{port}...")
    # We might not have the toml file created yet, so let's mock it or create it
    try:
        agent_card_dict = load_agent_card_toml(agent_name)
    except FileNotFoundError:
        # Fallback if TOML missing
        agent_card_dict = {
            "name": agent_name,
            "description": "WebShop Assessor",
            "version": "0.1.0",
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "capabilities": {},
            "skills": []
        }
        
    url = f"http://{host}:{port}"
    agent_card_dict["url"] = url

    request_handler = DefaultRequestHandler(
        agent_executor=WebShopGreenAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=AgentCard(**agent_card_dict),
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
