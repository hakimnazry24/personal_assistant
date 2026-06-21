"""In-process MCP server adapter for tools that run directly in Python.

This avoids the subprocess/stdio transport issues with anyio and Python 3.14.
Instead of spawning a separate process, tools are registered and called directly.

Use this for:
- Mock/test tools during development
- Python-native integrations (Google Calendar API, etc.)
- Any tool that doesn't need process isolation

For external MCP servers (Node.js, etc.), use MCPClient with stdio transport.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from agent.tools.base import ToolResult

logger = logging.getLogger(__name__)


class InProcessTool:
    """An in-process tool definition with its handler function."""

    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        input_schema: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.handler = handler
        self.input_schema = input_schema or {"type": "object", "properties": {}}

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict format for LLM tool definitions."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class InProcessMCPAdapter:
    """Adapter that mimics MCPManager but calls tools directly in-process.

    This is a drop-in replacement for MCPManager's tool-calling interface.
    It doesn't spawn subprocesses — tools run as direct Python function calls.

    Usage:
        adapter = InProcessMCPAdapter()
        adapter.register_tool(InProcessTool(...))
        tools = adapter.list_tools()
        result = await adapter.call_tool("tool_name", {"arg": "val"})
    """

    def __init__(self) -> None:
        self._tools: dict[str, InProcessTool] = {}
        self.started = True

    def register_tool(self, tool: InProcessTool) -> None:
        """Register a tool for in-process execution."""
        self._tools[tool.name] = tool
        logger.debug("Registered in-process tool: %s", tool.name)

    async def list_tools(self) -> list[dict[str, Any]]:
        """Return all registered tool definitions."""
        return [t.to_dict() for t in self._tools.values()]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool by name with the given arguments.

        Args:
            name: The tool name.
            arguments: Keyword arguments for the tool handler.

        Returns:
            The tool's return value (dict, list, str, etc.).

        Raises:
            KeyError: If the tool is not registered.
        """
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool '{name}' not found. Available: {list(self._tools.keys())}")

        try:
            result = tool.handler(**arguments)
            logger.info("Tool '%s' executed successfully.", name)
            return result
        except Exception as exc:
            logger.error("Tool '%s' failed: %s", name, exc)
            raise

    # ── MCPManager-compatible interface ───────────────────────────────

    async def start_all(self) -> None:
        """No-op for in-process adapter (tools are always available)."""
        self.started = True

    async def list_all_tools(self) -> list[dict[str, Any]]:
        """Alias for list_tools() — matches MCPManager interface."""
        return await self.list_tools()

    async def shutdown_all(self) -> None:
        """No-op for in-process adapter."""
        self.started = False


# ── Pre-built tool registries ──────────────────────────────────────────────

def create_calendar_tools(adapter: InProcessMCPAdapter | None = None) -> InProcessMCPAdapter:
    """Register calendar tools on an adapter (real API or mock, auto-detected).

    Uses real Google Calendar API when credentials are available,
    falls back to mock data otherwise.

    Args:
        adapter: Existing adapter to add tools to. Creates a new one if None.

    Returns:
        The adapter with calendar tools registered.
    """
    from agent.tools.calendar_google import get_calendar_handlers

    handlers = get_calendar_handlers()

    if adapter is None:
        adapter = InProcessMCPAdapter()

    adapter.register_tool(InProcessTool(
        name="list_events",
        description="List calendar events for a given date or date range. "
                    "Use date (YYYY-MM-DD) for a single day, or date_from/date_to for a range.",
        handler=handlers["list_events"],
        input_schema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "date_from": {
                    "type": "string",
                    "description": "Start of date range (YYYY-MM-DD)"
                },
                "date_to": {
                    "type": "string",
                    "description": "End of date range (YYYY-MM-DD)"
                },
            },
        },
    ))

    adapter.register_tool(InProcessTool(
        name="create_event",
        description="Create a new calendar event. Requires summary, start, and end times.",
        handler=handlers["create_event"],
        input_schema={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Event title/summary"
                },
                "start": {
                    "type": "string",
                    "description": "Start time in HH:MM format (24-hour)"
                },
                "end": {
                    "type": "string",
                    "description": "End time in HH:MM format (24-hour)"
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (defaults to today)"
                },
                "description": {
                    "type": "string",
                    "description": "Optional event description"
                },
                "location": {
                    "type": "string",
                    "description": "Optional event location"
                },
            },
            "required": ["summary", "start", "end"],
        },
    ))

    adapter.register_tool(InProcessTool(
        name="update_event",
        description="Update an existing calendar event by its ID.",
        handler=handlers["update_event"],
        input_schema={
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "The event ID to update"
                },
                "summary": {
                    "type": "string",
                    "description": "New title (optional)"
                },
                "start": {
                    "type": "string",
                    "description": "New start time (optional)"
                },
                "end": {
                    "type": "string",
                    "description": "New end time (optional)"
                },
                "date": {
                    "type": "string",
                    "description": "New date (optional)"
                },
            },
            "required": ["event_id"],
        },
    ))

    adapter.register_tool(InProcessTool(
        name="delete_event",
        description="Delete a calendar event by its ID.",
        handler=handlers["delete_event"],
        input_schema={
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "The event ID to delete"
                },
            },
            "required": ["event_id"],
        },
    ))

    return adapter
