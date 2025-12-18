"""White agent implementation for WebShop."""

import uvicorn
import dotenv
import json
import os
import asyncio
import google.generativeai as genai
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from a2a.utils import new_agent_text_message
from src.my_util import parse_tags

dotenv.load_dotenv()

# Configure Gemini
if "GEMINI_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def prepare_white_agent_card(url):
    skill = AgentSkill(
        id="shopping_fulfillment",
        name="Shopping Fulfillment",
        description="Handles shopping requests",
        tags=["general"],
        examples=[],
    )
    card = AgentCard(
        name="webshop_white_agent",
        description="Test agent for WebShop",
        url=url,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(),
        skills=[skill],
    )
    return card

class WebShopWhiteAgentExecutor(AgentExecutor):
    def __init__(self):
        # Store chat sessions: context_id -> ChatSession
        self.ctx_id_to_chat = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()
        
        # Initialize chat session if needed
        if context.context_id not in self.ctx_id_to_chat:
            # Initialize Gemini model with system instruction
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-lite",
                system_instruction="You are a helpful shopping assistant. You interact with a WebShop environment. Always output your action in JSON format: {\"action\": \"...\"} inside <json> tags."
            )
            self.ctx_id_to_chat[context.context_id] = model.start_chat(history=[])
            
        chat = self.ctx_id_to_chat[context.context_id]

        # Rate Limiting: Proactive delay to avoid burning out free tier quota (approx 15 RPM limit)
        print("White Agent: Waiting 5s to respect rate limits...")
        await asyncio.sleep(5)

        # Call Gemini with retries
        max_retries = 10
        base_delay = 5
        content = ""
        
        for attempt in range(max_retries):
            try:
                # chat.send_message is synchronous in this library version, but we are in an async function.
                # Ideally run in executor, but simple blocking here with async sleep is "okay" for this level of agent.
                response = chat.send_message(user_input)
                content = response.text
                break
            except Exception as e:
                error_str = str(e)
                print(f"Gemini Error (Attempt {attempt+1}/{max_retries}): {error_str}")
                
                # Check for rate limit or quota issues
                if "429" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"Rate limited. Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                
                # If not a rate limit, or out of retries, fail gracefully
                content = f"Error generating response: {e}"
                if attempt == max_retries - 1:
                    print("Max retries reached. Giving up.")
                else:
                    # For non-rate-limit errors, maybe we shouldn't retry? 
                    # But often transient network errors happen too. Let's retry carefully.
                    wait_time = 2
                    await asyncio.sleep(wait_time)


        await event_queue.enqueue_event(
            new_agent_text_message(content, context_id=context.context_id)
        )

    async def cancel(self, context, event_queue) -> None:
        raise NotImplementedError

def start_white_agent(agent_name="webshop_white_agent", host="localhost", port=9002):
    host = os.getenv("HOST", host)
    port = int(os.getenv("AGENT_PORT", port))
    agent_url = os.getenv("AGENT_URL", f"http://{host}:{port}")
    print(f"Starting white agent on {host}:{port}...")
    card = prepare_white_agent_card(agent_url)

    request_handler = DefaultRequestHandler(
        agent_executor=WebShopWhiteAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=card,
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
