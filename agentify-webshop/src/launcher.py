"""Launcher for WebShop Agentified Evaluation."""

import multiprocessing
import json
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.green_agent.agent import start_green_agent
from src.white_agent.agent import start_white_agent
from src.my_util import wait_agent_ready, send_message

async def launch_evaluation():
    # Start Green Agent
    print("Launching Green Agent...")
    green_host, green_port = "localhost", 9001
    green_url = f"http://{green_host}:{green_port}"
    p_green = multiprocessing.Process(
        target=start_green_agent, args=("webshop_green_agent", green_host, green_port)
    )
    p_green.start()
    
    if not await wait_agent_ready(green_url):
        print("Green agent failed to start.")
        p_green.terminate()
        return

    print("Green Agent Ready.")

    # Start White Agent
    print("Launching White Agent...")
    white_host, white_port = "localhost", 9002
    white_url = f"http://{white_host}:{white_port}"
    p_white = multiprocessing.Process(
        target=start_white_agent, args=("webshop_white_agent", white_host, white_port)
    )
    p_white.start()

    if not await wait_agent_ready(white_url):
        print("White agent failed to start.")
        p_green.terminate()
        p_white.terminate()
        return

    print("White Agent Ready.")

    # Configure Task
    # We pass the configuration for the WebShop environment
    env_config = {
        "num_products": 1000,
        "human_goals": True
        # Add other webshop-specific configs here if needed
    }

    task_text = f"""
Your task is to instantiate WebShop to test the agent located at:
<white_agent_url>
{white_url}/
</white_agent_url>

You should use the following env configuration:
<env_config>
{json.dumps(env_config, indent=2)}
</env_config>
"""

    print("Sending assessment request to Green Agent...")
    try:
        response = await send_message(green_url, task_text)
        print("\n--- Assessment Result ---")
        # We expect a single text part in the response
        if response.root and response.root.result and response.root.result.parts:
             print(response.root.result.parts[0].root.text)
        else:
             print("Received unexpected response format:", response)
             
    except Exception as e:
        print(f"Error during assessment: {e}")

    print("\nTerminating Agents...")
    p_green.terminate()
    p_white.terminate()
    p_green.join()
    p_white.join()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(launch_evaluation())
