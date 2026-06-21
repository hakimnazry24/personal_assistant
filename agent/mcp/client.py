"""Generic MCP client that connects to an MCP server via stdio transport.

Uses the official mcp Python SDK to launch an MCP server as a subprocess
and communicate with it over standard input/output (JSON-RPC).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Raised when an MCP client operation fails."""


class MCPClient:
    """Generic MCP client for connecting to a single MCP server via stdio.

    Launches the MCP server as a subprocess and communicates using the
    Model Context Protocol over JSON-RPC on stdin/stdout.

    Usage:
        client = MCPClient(command="npx", args=["-y", "@scope/mcp-server"])
        await client.connect()
        tools = await client.list_tools()
        result = await client.call_tool("tool_name", {"arg": "value"})
        await client.close()
    """

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        name: str = "unnamed",
    ) -> None:
        """Initialize the MCP client.

        Args:
            command: Executable to run (e.g., "npx", "python", "node").
            args: Command-line arguments for the server process.
            env: Extra environment variables to pass to the server subprocess.
            name: Human-readable name for logging and debugging.
        """
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.name = name

        # Set after connect()
        self._session: ClientSession | None = None
        self._read_stream = None
        self._write_stream = None
        self._connected = False

    @property
    def connected(self) -> bool:
        """Whether this client is currently connected to its MCP server."""
        return self._connected

    async def connect(self) -> None:
        """Launch the MCP server subprocess and establish a session.

        Raises:
            MCPClientError: If the server process fails to start or the
                            MCP handshake fails.
        """
        if self._connected:
            logger.warning("MCP client '%s' is already connected.", self.name)
            return

        logger.info("Starting MCP server '%s': %s %s",
                      self.name, self.command, " ".join(self.args))

        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env if self.env else None,
            )

            # stdio_client returns a context manager with (read, write) streams
            self._read_stream, self._write_stream = await stdio_client(server_params).__aenter__()

            self._session = ClientSession(
                self._read_stream, self._write_stream
            )
            await self._session.initialize()

            self._connected = True
            logger.info("MCP client '%s' connected successfully.", self.name)

        except Exception:
            self._connected = False
            raise MCPClientError(
                f"Failed to connect MCP client '{self.name}' "
                f"({self.command} {' '.join(self.args)})"
            ) from None

    async def list_tools(self) -> list[dict[str, Any]]:
        """Retrieve the list of tools exposed by this MCP server.

        Returns:
            List of tool definitions, each with 'name', 'description',
            and 'inputSchema' keys.

        Raises:
            MCPClientError: If not connected or the call fails.
        """
        self._ensure_connected()

        try:
            result = await self._session.list_tools()  # type: ignore[union-attr]
            return [tool.model_dump() for tool in result.tools]
        except Exception as exc:
            raise MCPClientError(
                f"Failed to list tools for MCP client '{self.name}': {exc}"
            ) from exc

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server.

        Args:
            name: The tool name (as returned by list_tools).
            arguments: Keyword arguments to pass to the tool.

        Returns:
            The tool's result content.

        Raises:
            MCPClientError: If not connected or the tool call fails.
        """
        self._ensure_connected()

        try:
            result = await self._session.call_tool(name, arguments)  # type: ignore[union-attr]
            return result.content
        except Exception as exc:
            raise MCPClientError(
                f"Tool '{name}' failed on MCP client '{self.name}': {exc}"
            ) from exc

    async def close(self) -> None:
        """Gracefully close the MCP session and terminate the subprocess."""
        if not self._connected:
            return

        logger.info("Closing MCP client '%s'.", self.name)
        try:
            if self._session:
                await self._session.close()
        except Exception:
            logger.exception("Error closing MCP session for '%s'.", self.name)
        finally:
            self._session = None
            self._read_stream = None
            self._write_stream = None
            self._connected = False

    def _ensure_connected(self) -> None:
        """Raise if the client is not connected."""
        if not self._connected:
            raise MCPClientError(
                f"MCP client '{self.name}' is not connected. Call connect() first."
            )

    async def __aenter__(self) -> MCPClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
