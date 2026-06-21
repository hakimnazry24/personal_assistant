"""MCP server exposing Google Calendar tools (mock data for testing).

Run with:
    python -m agent.mcp.servers.calendar_server

This server uses FastMCP to expose calendar tools via stdio transport.
Currently returns mock data. Swap in real Google Calendar API calls
when credentials are available.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# ── Mock data ──────────────────────────────────────────────────────────────

_MOCK_EVENTS: list[dict] = [
    {
        "id": "evt_001",
        "summary": "Morning Standup",
        "start": "09:00",
        "end": "09:30",
        "date": None,  # recurring daily
    },
    {
        "id": "evt_002",
        "summary": "Lunch with Sarah",
        "start": "12:30",
        "end": "13:30",
        "date": "2026-06-22",
    },
    {
        "id": "evt_003",
        "summary": "Project Review",
        "start": "15:00",
        "end": "16:00",
        "date": "2026-06-22",
    },
    {
        "id": "evt_004",
        "summary": "Dentist Appointment",
        "start": "10:00",
        "end": "11:00",
        "date": "2026-06-23",
    },
]

_next_id = 100


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _tomorrow_str() -> str:
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


# ── Server ─────────────────────────────────────────────────────────────────

server = FastMCP(
    name="Google Calendar",
    instructions="MCP server for Google Calendar. Currently in mock mode.",
)


@server.tool(name="list_events", description="List calendar events for a given date or date range.")
def list_events(
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Return mock calendar events filtered by date.

    Args:
        date: A single date in YYYY-MM-DD format. If provided, returns
              events for that day plus recurring events.
        date_from: Start of date range (YYYY-MM-DD).
        date_to: End of date range (YYYY-MM-DD).

    Returns:
        List of event dicts with id, summary, start, end, date.
    """
    target = date or _today_str()

    results = []
    for evt in _MOCK_EVENTS:
        evt_date = evt.get("date")
        if evt_date is None:
            # Recurring event — include for any date
            results.append(dict(evt))
        elif date_from and date_to:
            if date_from <= evt_date <= date_to:
                results.append(dict(evt))
        elif evt_date == target:
            results.append(dict(evt))

    logger.info("list_events: %d event(s) for %s", len(results), target)
    return results


@server.tool(name="create_event", description="Create a new calendar event.")
def create_event(
    summary: str,
    start: str,
    end: str,
    date: str | None = None,
    description: str | None = None,
    location: str | None = None,
) -> dict:
    """Create a mock calendar event.

    Args:
        summary: Event title.
        start: Start time (HH:MM).
        end: End time (HH:MM).
        date: Date (YYYY-MM-DD), defaults to today.
        description: Optional event description.
        location: Optional event location.

    Returns:
        The created event dict.
    """
    global _next_id
    event_date = date or _today_str()
    new_event = {
        "id": f"evt_{_next_id:03d}",
        "summary": summary,
        "start": start,
        "end": end,
        "date": event_date,
        "description": description,
        "location": location,
    }
    _next_id += 1
    _MOCK_EVENTS.append(new_event)
    logger.info("create_event: '%s' on %s at %s–%s", summary, event_date, start, end)
    return new_event


@server.tool(name="update_event", description="Update an existing calendar event.")
def update_event(
    event_id: str,
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    date: str | None = None,
) -> dict:
    """Update a mock calendar event by ID.

    Args:
        event_id: The event ID to update.
        summary: New title (optional).
        start: New start time (optional).
        end: New end time (optional).
        date: New date (optional).

    Returns:
        The updated event dict, or error if not found.
    """
    for evt in _MOCK_EVENTS:
        if evt["id"] == event_id:
            if summary:
                evt["summary"] = summary
            if start:
                evt["start"] = start
            if end:
                evt["end"] = end
            if date:
                evt["date"] = date
            logger.info("update_event: '%s' updated", event_id)
            return dict(evt)

    return {"error": f"Event '{event_id}' not found."}


@server.tool(name="delete_event", description="Delete a calendar event by ID.")
def delete_event(event_id: str) -> dict:
    """Delete a mock calendar event by ID.

    Args:
        event_id: The event ID to delete.

    Returns:
        Confirmation dict or error.
    """
    global _MOCK_EVENTS
    for i, evt in enumerate(_MOCK_EVENTS):
        if evt["id"] == event_id:
            deleted = _MOCK_EVENTS.pop(i)
            logger.info("delete_event: '%s' (%s) deleted", event_id, deleted["summary"])
            return {"deleted": True, "event_id": event_id, "summary": deleted["summary"]}

    return {"error": f"Event '{event_id}' not found."}


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server.run(transport="stdio")
