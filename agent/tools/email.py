"""Gmail integration tool (placeholder)."""

from agent.tools.base import BaseTool, ToolResult


class EmailTool(BaseTool):
    """Tool for interacting with Gmail.

    This is a placeholder. Full implementation will be added
    when Gmail integration is needed.
    """

    name = "gmail"
    description = "Manage Gmail: send, read, search, and organize emails."

    async def execute(self, **kwargs) -> ToolResult:
        """Execute email operations.

        Args:
            action: The action to perform (send, read, search, delete)
            **kwargs: Additional parameters for the action

        Returns:
            ToolResult with the operation status
        """
        action = kwargs.get("action", "read")
        return ToolResult(
            success=False,
            message=f"Gmail integration not yet implemented. Action '{action}' received.",
            data={"action": action},
        )
