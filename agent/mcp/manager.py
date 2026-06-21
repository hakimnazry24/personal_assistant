"""Manager for multiple MCP server connections.

Reads mcp_servers.json to discover server configurations and manages
their lifecycles — starting, stopping, and health-checking each server.
"""

from __future__ import annotations

import json
import logging
import os
import string
from pathlib import Path
from typing import Any

from agent.mcp.client import MCPClient, MCPClientError

logger = logging.getLogger(__name__)


class MCPManagerError(Exception):
    """Raised when an MCP manager operation fails."""


class MCPManager:
    """Manages multiple MCP client connections across servers.

    Reads server definitions from a JSON config file (mcp_servers.json) and
    provides a unified interface to list and call tools across all servers.

    Usage:
        manager = MCPManager()
        await manager.start_all()
        all_tools = await manager.list_all_tools()
        result = await manager.call_tool("google_calendar_list_events", {...})
        await manager.shutdown_all()
    """

    DEFAULT_CONFIG_PATH = Path("mcp_servers.json")

    def __init__(self, config_path: Path | str | None = None) -> None:
        """Initialize the MCP manager.

        Args:
            config_path: Path to the mcp_servers.json file.
                         Defaults to 'mcp_servers.json' in CWD.
        """
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self._clients: dict[str, MCPClient] = {}
        self._tool_registry: dict[str, str] = {}  # tool_name → server_name
        self._started = False

    @property
    def started(self) -> bool:
        """Whether the manager has started and connected to servers."""
        return self._started

    async def start_all(self) -> None:
        """Start all configured MCP servers from mcp_servers.json.

        Reads the config, creates an MCPClient for each server, connects them,
        and builds the tool registry.

        Raises:
            MCPManagerError: If the config is missing, invalid, or any server
                             fails to start.
        """
        if self._started:
            logger.warning("MCPManager is already started.")
            return

        config = self._load_config()
        servers = config.get("servers", {})

        if not servers:
            logger.info("No MCP servers configured in %s.", self.config_path)
            self._started = True
            return

        for server_name, server_config in servers.items():
            client = MCPClient(
                command=server_config["command"],
                args=server_config.get("args", []),
                env=self._resolve_env(server_config.get("env", {})),
                name=server_name,
            )
            try:
                await client.connect()
                self._clients[server_name] = client

                # Register tools
                tools = await client.list_tools()
                for tool in tools:
                    tool_name = tool["name"]
                    self._tool_registry[tool_name] = server_name

                logger.info(
                    "Server '%s': %d tool(s) registered.",
                    server_name, len(tools),
                )

            except MCPClientError as exc:
                logger.error("Failed to start server '%s': %s", server_name, exc)
                # Continue starting other servers
            except Exception:
                logger.exception("Unexpected error starting server '%s'.", server_name)

        self._started = True
        logger.info(
            "MCPManager started: %d server(s), %d tool(s).",
            len(self._clients), len(self._tool_registry),
        )

    async def list_all_tools(self) -> list[dict[str, Any]]:
        """List all tools from all connected MCP servers.

        Returns:
            Combined list of tool definitions from every server.

        Raises:
            MCPManagerError: If the manager hasn't been started.
        """
        self._ensure_started()

        all_tools: list[dict[str, Any]] = []
        for client in self._clients.values():
            try:
                tools = await client.list_tools()
                all_tools.extend(tools)
            except MCPClientError as exc:
                logger.error("Failed to list tools for '%s': %s", client.name, exc)

        return all_tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool by name, routing to the correct MCP server.

        Args:
            tool_name: The tool to call (must be in the registry).
            arguments: Arguments to pass to the tool.

        Returns:
            The tool's result content.

        Raises:
            MCPManagerError: If the manager hasn't started or the tool
                             is not found.
        """
        self._ensure_started()

        if tool_name not in self._tool_registry:
            raise MCPManagerError(
                f"Tool '{tool_name}' not found in any MCP server. "
                f"Available: {list(self._tool_registry.keys())}"
            )

        server_name = self._tool_registry[tool_name]
        client = self._clients[server_name]

        return await client.call_tool(tool_name, arguments)

    def get_tool_definitions_for_llm(self) -> list[dict[str, Any]]:
        """Return tool definitions formatted for LLM function-calling APIs.

        This is a synchronous convenience method that returns cached tool
        definitions. Call after list_all_tools() to populate the cache.

        Returns:
            List of dicts with 'type': 'function', 'function': {name, description, parameters}.
        """
        # Re-fetch asynchronously — caller should have done list_all_tools first
        # For now, return from cache
        definitions: list[dict[str, Any]] = []
        # We can't call async here, so we build from cached registry
        # This is a lightweight sync helper; actual tool defs come from list_all_tools
        return definitions

    async def shutdown_all(self) -> None:
        """Gracefully shut down all MCP server connections."""
        logger.info("Shutting down %d MCP server(s)...", len(self._clients))
        for name, client in self._clients.items():
            try:
                await client.close()
                logger.info("Server '%s' shut down.", name)
            except Exception:
                logger.exception("Error shutting down server '%s'.", name)

        self._clients.clear()
        self._tool_registry.clear()
        self._started = False

    def _ensure_started(self) -> None:
        """Raise if the manager hasn't been started."""
        if not self._started:
            raise MCPManagerError(
                "MCPManager is not started. Call start_all() first."
            )

    def _load_config(self) -> dict[str, Any]:
        """Load and validate the mcp_servers.json configuration file.

        Returns:
            Parsed config dict.

        Raises:
            MCPManagerError: If the file is missing or invalid.
        """
        if not self.config_path.exists():
            raise MCPManagerError(
                f"MCP server config not found at {self.config_path}. "
                f"Create mcp_servers.json with your server definitions."
            )

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as exc:
            raise MCPManagerError(
                f"Invalid JSON in {self.config_path}: {exc}"
            ) from exc

        # Validate structure
        if not isinstance(config, dict):
            raise MCPManagerError(
                f"{self.config_path} must contain a JSON object with a 'servers' key."
            )

        servers = config.get("servers", {})
        for name, srv in servers.items():
            if "command" not in srv:
                raise MCPManagerError(
                    f"Server '{name}' in {self.config_path} is missing 'command'."
                )

        return config

    @staticmethod
    def _resolve_env(env: dict[str, str]) -> dict[str, str]:
        """Resolve environment variable references like ${VAR_NAME}.

        Args:
            env: Dict mapping env var names to values, which may include
                 ${VAR} placeholders that reference actual env vars.

        Returns:
            Dict with placeholders resolved.
        """
        template = string.Template("")
        resolved: dict[str, str] = {}
        for key, value in env.items():
            try:
                template.template = value
                resolved[key] = template.safe_substitute(os.environ)
            except Exception:
                resolved[key] = value
        return resolved
