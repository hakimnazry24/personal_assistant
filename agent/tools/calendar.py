"""Google Calendar integration tool (placeholder)."""

from agent.tools.base import BaseTool, ToolResult


class CalendarTool(BaseTool):
    """Tool for interacting with Google Calendar.

    This is a placeholder. Full implementation will be added
    when Google Calendar integration is needed.
    """

    name = "google_calendar"
    description = "Manage Google Calendar events: create, read, update, and delete events."

    async def execute(self, **kwargs) -> ToolResult:
        """Execute calendar operations.

        Args:
            action: The action to perform (list, create, update, delete)
            **kwargs: Additional parameters for the action

        Returns:
            ToolResult with the operation status
        """
        action = kwargs.get("action", "list")
        return ToolResult(
            success=False,
            message=f"Calendar integration not yet implemented. Action '{action}' received.",
            data={"action": action},
        )
