"""
Script to reproduce WebShop benchmark results quantitatively.
Runs a batch of evaluations with fixed seeds to ensure deterministic reproducibility.
"""

import multiprocessing
import json
import asyncio
import sys
import os
import time
import statistics

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.green_agent.agent import start_green_agent
from src.white_agent.agent import start_white_agent
from src.my_util import wait_agent_ready, send_message

async def run_batch_evaluation():
    # 1. Start Agents on dedicated ports for reproduction
    green_host, green_port = "localhost", 9011
    white_host, white_port = "localhost", 9012
    
    green_url = f"http://{green_host}:{green_port}"
    white_url = f"http://{white_host}:{white_port}"

    print(f"Starting Green Agent on {green_port}...")
    p_green = multiprocessing.Process(
        target=start_green_agent, args=("webshop_green_repro", green_host, green_port)
    )
    p_green.start()
    
    print(f"Starting White Agent on {white_port}...")
    p_white = multiprocessing.Process(
        target=start_white_agent, args=("webshop_white_repro", white_host, white_port)
    )
    p_white.start()

    # Wait for startup
    if not await wait_agent_ready(green_url) or not await wait_agent_ready(white_url):
        print("Failed to start agents.")
        p_green.terminate()
        p_white.terminate()
        return

    print("Agents ready. Starting benchmark reproduction...")
    
    # 2. Define Test Set (Fixed Seeds)
    seeds = [42, 43, 44, 45, 46]
    results = []
    
    for seed in seeds:
        print(f"\nEvaluating Seed: {seed}")
        
        env_config = {
            "num_products": 1000,
            "human_goals": True,
            "seed": seed
        }

        task_text = f"""
Your task is to instantiate WebShop to test the agent located at:
<white_agent_url>
{white_url}/
</white_agent_url>

You should use the following env configuration:
<env_config>
{json.dumps(env_config)}
</env_config>
"""
        try:
            # Send request to Green Agent
            # Increase timeout for the whole task
            response = await send_message(green_url, task_text)
            
            # Parse text response to find metrics
            if response.root and response.root.result and response.root.result.parts:
                text = response.root.result.parts[0].root.text
                print(f"Result: {text.strip()}")
                
                # Extract JSON metrics from the text output
                # The output format is: "Finished. White agent success: ...\nMetrics: {...}"
                metrics_start = text.find("Metrics: ") + len("Metrics: ")
                metrics_json = text[metrics_start:].strip()
                metrics = json.loads(metrics_json)
                
                results.append(metrics)
            else:
                print("Error: Empty response from Green Agent")
                
        except Exception as e:
            print(f"Error evaluating seed {seed}: {e}")

    # 3. Aggregate Results
    if results:
        avg_reward = statistics.mean(r["reward"] for r in results)
        success_rate = statistics.mean(1.0 if r["success"] else 0.0 for r in results) * 100
        avg_steps = statistics.mean(r["steps"] for r in results)
        avg_efficiency = statistics.mean(r["efficiency"] for r in results)
        
        print("\n" + "="*40)
        print("QUANTITATIVE BENCHMARK RESULTS (Reproduction)")
        print("="*40)
        print(f"Seeds Evaluated: {seeds}")
        print(f"Average Reward:  {avg_reward:.4f}")
        print(f"Success Rate:    {success_rate:.1f}%")
        print(f"Average Steps:   {avg_steps:.1f}")
        print(f"Avg Efficiency:  {avg_efficiency:.4f}")
        print("="*40)
    else:
        print("No results collected.")

    # 4. Cleanup
    print("Terminating agents...")
    p_green.terminate()
    p_white.terminate()
    p_green.join()
    p_white.join()

if __name__ == "__main__":
    asyncio.run(run_batch_evaluation())
