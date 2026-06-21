"""Core agent implementation using OpenAI SDK for DeepSeek.

Supports two modes:
- Chat-only: simple text conversation (no tools)
- Tool-calling: LLM can invoke MCP tools like calendar, email, etc.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from openai import OpenAI

from config.settings import settings

logger = logging.getLogger(__name__)


@runtime_checkable
class ToolProvider(Protocol):
    """Protocol for any object that can list and call tools."""

    started: bool

    async def list_all_tools(self) -> list[dict[str, Any]]: ...
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any: ...
    async def shutdown_all(self) -> None: ...


class Agent:
    """Personal Assistant Agent powered by DeepSeek V4 Pro."""

    SYSTEM_PROMPT = """You are a helpful personal assistant named {name}.
Current date: {current_date}.

You have access to tools that let you interact with the user's services:
- Google Calendar: list, create, update, and delete events
- More tools will be added over time (Gmail, WhatsApp, Telegram).

Rules:
1. Use tools when the user asks you to do something actionable (e.g., check
   calendar, create an event). Do NOT make up data — call the tool.
2. Be concise and friendly. Summarize tool results in natural language.
3. When listing events, present them in a clear, chronological format.
4. When a tool returns an error, tell the user what went wrong.
5. If you don't have a tool for something, explain that honestly."""

    def __init__(self, tool_provider: ToolProvider | None = None) -> None:
        """Initialize the agent.

        Args:
            tool_provider: Optional tool provider (MCPManager or
                           InProcessMCPAdapter). If None, chat-only mode.
        """
        settings.validate()

        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self.model = settings.DEEPSEEK_MODEL
        self.tool_provider = tool_provider
        self.max_tool_rounds = settings.AGENT_MAX_TOOL_ROUNDS

        self.system_prompt = self.SYSTEM_PROMPT.format(
            name=settings.AGENT_NAME,
            current_date=datetime.now().strftime("%A, %B %d, %Y"),
        )

    @property
    def has_tools(self) -> bool:
        """Whether the agent has tools available."""
        return self.tool_provider is not None and self.tool_provider.started

    # ── Chat-only methods (no tools) ───────────────────────────────────

    def chat(self, user_message: str) -> str:
        """Send a single message and get a response (no history, no tools)."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=settings.AGENT_MAX_TOKENS,
                temperature=settings.AGENT_TEMPERATURE,
            )
            return response.choices[0].message.content or "(no response)"
        except Exception as e:
            return f"Error communicating with DeepSeek API: {e}"

    def chat_with_history(self, messages: list[dict[str, str]]) -> str:
        """Send conversation with history and get a response (no tools)."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system_prompt}, *messages],
                max_tokens=settings.AGENT_MAX_TOKENS,
                temperature=settings.AGENT_TEMPERATURE,
            )
            return response.choices[0].message.content or "(no response)"
        except Exception as e:
            return f"Error communicating with DeepSeek API: {e}"

    # ── Tool-calling methods ───────────────────────────────────────────

    async def chat_with_tools(
        self, messages: list[dict[str, Any]]
    ) -> str:
        """Send conversation with tool support.

        The agent sends the conversation + available tool definitions to the
        LLM. If the LLM responds with tool_calls, the agent executes them
        via the MCPManager and loops until the LLM gives a final text response.

        Args:
            messages: Conversation history as list of message dicts.
                      Each dict has at least 'role' and 'content'.

        Returns:
            The final text response from the LLM.
        """
        if not self.has_tools:
            # Fall back to chat-only mode
            simple_msgs = [
                {"role": m["role"], "content": str(m.get("content", ""))}
                for m in messages
                if "role" in m
            ]
            return self.chat_with_history(simple_msgs)

        # Get tool definitions from MCP servers
        tool_defs = await self._build_tool_definitions()

        full_messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            *messages,
        ]

        for round_num in range(self.max_tool_rounds):
            logger.debug(
                "Tool-calling round %d/%d", round_num + 1, self.max_tool_rounds
            )

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    tools=tool_defs if tool_defs else None,
                    max_tokens=settings.AGENT_MAX_TOKENS,
                    temperature=settings.AGENT_TEMPERATURE,
                )
            except Exception as e:
                logger.exception(
                    "DeepSeek API error in round %d", round_num
                )
                return f"Error communicating with DeepSeek API: {e}"

            msg = response.choices[0].message

            # Model gave a direct text response → done
            if msg.content and not msg.tool_calls:
                return msg.content

            # Model wants to call tools
            if msg.tool_calls:
                # Record assistant's tool-call request
                assistant_msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
                full_messages.append(assistant_msg)

                # Execute each tool call
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    logger.info("Calling tool: %s(%s)", tool_name, tool_args)

                    try:
                        assert self.tool_provider is not None
                        result = await self.tool_provider.call_tool(
                            tool_name, tool_args
                        )
                        result_str = json.dumps(result, default=str)
                    except Exception as exc:
                        result_str = json.dumps({"error": str(exc)})
                        logger.error("Tool '%s' failed: %s", tool_name, exc)

                    full_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_str,
                    })

                # Loop back — LLM processes tool results next round
                continue

            # No content and no tool calls (edge case)
            if msg.content:
                return msg.content
            return "(no response)"

        logger.warning(
            "Reached max tool-calling rounds (%d)", self.max_tool_rounds
        )
        return (
            "I went through several rounds of tool calls but couldn't "
            "complete your request. Please try simplifying it."
        )

    async def _build_tool_definitions(self) -> list[dict[str, Any]]:
        """Fetch tool definitions from MCP servers in OpenAI format."""
        if not self.tool_provider:
            return []

        try:
            raw_tools = await self.tool_provider.list_all_tools()
        except Exception:
            logger.exception("Failed to list MCP tools")
            return []

        definitions: list[dict[str, Any]] = []
        for tool in raw_tools:
            definitions.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", "unknown"),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {
                        "type": "object",
                        "properties": {},
                    }),
                },
            })

        return definitions


def test_agent() -> bool:
    """Quick test to verify the agent can communicate with DeepSeek."""
    agent = Agent()
    response = agent.chat("Hello! Please respond with just: 'I am working.'")
    print(f"Agent response: {response}")
    return "working" in response.lower() or "I am" in response

