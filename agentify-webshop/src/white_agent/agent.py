"""White agent implementation for WebShop."""

import uvicorn
import dotenv
import json
import os
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
                model_name="gemini-2.5-pro",
                system_instruction="You are a helpful shopping assistant. You interact with a WebShop environment. Always output your action in JSON format: {\"action\": \"...\"} inside <json> tags."
            )
            self.ctx_id_to_chat[context.context_id] = model.start_chat(history=[])
            
        chat = self.ctx_id_to_chat[context.context_id]

        # Call Gemini
        try:
            response = chat.send_message(user_input)
            content = response.text
        except Exception as e:
            content = f"Error generating response: {e}"
            print(f"Gemini Error: {e}")

        await event_queue.enqueue_event(
            new_agent_text_message(content, context_id=context.context_id)
        )

    async def cancel(self, context, event_queue) -> None:
        raise NotImplementedError

def start_white_agent(agent_name="webshop_white_agent", host="localhost", port=9002):
    print(f"Starting white agent on {host}:{port}...")
    url = f"http://{host}:{port}"
    card = prepare_white_agent_card(url)

    request_handler = DefaultRequestHandler(
        agent_executor=WebShopWhiteAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=card,
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)
