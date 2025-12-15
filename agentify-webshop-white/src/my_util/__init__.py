import re
import json
import asyncio
import time
import uuid
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    Message,
    Part,
    TextPart,
    Role,
    SendMessageRequest,
)

async def _get_agent_card(url: str):
    async with httpx.AsyncClient() as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=url)
        return await resolver.get_agent_card()


async def send_message(url, message, context_id=None, task_id=None):
    agent_card = await _get_agent_card(url)
    async with httpx.AsyncClient(timeout=120.0) as http_client:
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)
        params = MessageSendParams(
            message=Message(
                role=Role.user,
                parts=[Part(TextPart(text=message))],
                message_id=uuid.uuid4().hex,
                context_id=context_id,
                task_id=task_id,
            )
        )
        request = SendMessageRequest(id=uuid.uuid4().hex, params=params)
        return await client.send_message(request=request)

async def wait_agent_ready(url, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            card = await _get_agent_card(url)
            if card:
                return True
        except Exception as e:
            print(f"Liveness check failed: {e}")
            pass
        await asyncio.sleep(1)
    return False

def parse_tags(text):
    """Parse XML-like tags from text."""
    tags = {}
    pattern = r"<(\w+)>(.*?)</\1>"
    matches = re.findall(pattern, text, re.DOTALL)
    for tag, content in matches:
        tags[tag] = content.strip()
    return tags
