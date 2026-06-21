"""CLI interface for the Personal Assistant agent.

Supports both chat-only mode and tool-calling mode (when MCP servers are
configured and available).
"""

from __future__ import annotations

import asyncio
import logging
import sys

from agent.core import Agent
from agent.mcp.adapters import InProcessMCPAdapter, create_calendar_tools

logger = logging.getLogger(__name__)


def run_cli() -> None:
    """Run the interactive CLI loop."""
    asyncio.run(_run_cli_async())


async def _run_cli_async() -> None:  # noqa: C901
    """Async CLI loop with MCP support."""
    print("=" * 50)
    print("  🤖  Personal Assistant Agent")
    print("  Powered by DeepSeek V4 Pro")
    print("=" * 50)
    print()

    # ── Start MCP servers ──────────────────────────────────────────────
    print("🔧 Loading built-in tools...")
    try:
        tool_provider = create_calendar_tools()
        tools = await tool_provider.list_all_tools()
        print(f"   {len(tools)} tool(s) available (calendar).")
    except Exception as e:
        print(f"⚠️  Failed to load tools: {e}")
        tool_provider = None
    print()

    # ── Init agent ─────────────────────────────────────────────────────
    try:
        agent = Agent(tool_provider=tool_provider)
        print("✅ Agent initialized successfully.\n")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please set your DEEPSEEK_API_KEY in the .env file.")
        if tool_provider:
            await tool_provider.shutdown_all()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        if tool_provider:
            await tool_provider.shutdown_all()
        sys.exit(1)

    print("Type your message and press Enter to chat.")
    print("Commands:")
    print("  /exit  - Exit the assistant")
    print("  /clear - Clear conversation history")
    print("  /help  - Show this help message")
    if agent.has_tools:
        print("  /tools - List available tools")
    print()

    messages: list[dict[str, str]] = []

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye! 👋")
                break

            if not user_input:
                continue

            # ── Handle commands ────────────────────────────────────────
            if user_input.startswith("/"):
                command = user_input.lower()
                if command == "/exit":
                    print("Goodbye! 👋")
                    break
                elif command == "/clear":
                    messages.clear()
                    print("🔄 Conversation history cleared.\n")
                    continue
                elif command == "/help":
                    print("\nCommands:")
                    print("  /exit  - Exit the assistant")
                    print("  /clear - Clear conversation history")
                    print("  /help  - Show this help message")
                    if agent.has_tools:
                        print("  /tools - List available tools")
                    print()
                    continue
                elif command == "/tools" and agent.has_tools:
                    tools = await tool_provider.list_all_tools()
                    print(f"\n📦 {len(tools)} tool(s) available:\n")
                    for t in tools:
                        name = t.get("name", "unknown")
                        desc = t.get("description", "no description")
                        print(f"  • {name}")
                        print(f"    {desc}\n")
                    continue
                else:
                    print(f"Unknown command: {user_input}")
                    print("Type /help for available commands.\n")
                    continue

            # ── Send message to agent ──────────────────────────────────
            messages.append({"role": "user", "content": user_input})
            print("Assistant: ", end="", flush=True)

            if agent.has_tools:
                response = await agent.chat_with_tools(messages)
            else:
                response = agent.chat_with_history(messages)

            print(response)
            print()

            messages.append({"role": "assistant", "content": response})

    finally:
        if tool_provider:
            await tool_provider.shutdown_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    run_cli()
