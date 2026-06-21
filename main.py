#!/usr/bin/env python3
"""Personal Assistant Agent - Main Entry Point.

Usage:
    python main.py              # Start interactive CLI mode
    python main.py --test       # Quick test: verify agent can chat
    python main.py --test-tools # Full test: verify MCP tools + tool-calling
"""

import asyncio
import sys

from agent.cli import run_cli


async def test_tools() -> bool:
    """Test the full tool-calling pipeline using in-process tools."""
    from agent.core import Agent
    from agent.mcp.adapters import create_calendar_tools

    print("🔧 Setting up in-process calendar tools...")
    tool_provider = create_calendar_tools()
    tools = await tool_provider.list_all_tools()
    print(f"✅ {len(tools)} tool(s) registered.\n")

    agent = Agent(tool_provider=tool_provider)

    # Test 1: Ask the agent to list events using the tool
    print("─" * 50)
    print("Test: 'What's on my calendar for June 22, 2026?'")
    print("─" * 50)

    messages = [{"role": "user", "content": "What's on my calendar for June 22, 2026?"}]
    response = await agent.chat_with_tools(messages)
    print(f"Assistant: {response}\n")

    # Test 2: Ask the agent to create an event
    print("─" * 50)
    print("Test: 'Create a meeting called Test Meeting at 2pm for 1 hour'")
    print("─" * 50)

    messages = [{"role": "user", "content": "Create a meeting called 'Test Meeting' tomorrow at 14:00 for 1 hour on my calendar."}]
    response = await agent.chat_with_tools(messages)
    print(f"Assistant: {response}\n")

    # Simple check: did the agent actually use tools?
    success = "event" in response.lower() or "calendar" in response.lower() or "meeting" in response.lower()
    return success


def main() -> None:
    args = sys.argv[1:]

    if "--test" in args:
        from agent.core import test_agent
        print("Running agent test...\n")
        success = test_agent()
        if success:
            print("\n✅ Agent is working correctly!")
        else:
            print("\n⚠️  Agent test completed but response was unexpected.")
            print("   Check your API key and network connection.")

    elif "--test-tools" in args:
        print("Running MCP + tool-calling test...\n")
        success = asyncio.run(test_tools())
        if success:
            print("✅ Tool-calling test passed!")
        else:
            print("⚠️  Tool-calling test completed but result was unexpected.")

    else:
        run_cli()


if __name__ == "__main__":
    main()
