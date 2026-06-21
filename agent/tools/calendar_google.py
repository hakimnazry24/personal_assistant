"""Real Google Calendar integration using Google Calendar API.

Replaces the mock handlers in calendar_server.py with actual API calls.
Falls back to mock mode when credentials are not configured.

Usage:
    handlers = get_calendar_handlers()  # returns real or mock automatically
    events = handlers["list_events"](date="2026-06-22")
"""

from __future__ import annotations

import logging
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

_TOKEN_PATH = Path("token_calendar.pickle")
_CREDENTIALS_PATH = Path("credentials_calendar.json")

# ── Google API helpers ────────────────────────────────────────────────────

def _get_calendar_service():
    """Build and return an authenticated Google Calendar API service.

    Returns None if credentials are not configured or auth fails.
    """
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    creds = None

    # Load saved token
    if _TOKEN_PATH.exists():
        with open(_TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    # Refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif _CREDENTIALS_PATH.exists():
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)
        else:
            logger.warning(
                "Google Calendar credentials not found at %s. "
                "Download OAuth credentials from Google Cloud Console "
                "and save as credentials_calendar.json.",
                _CREDENTIALS_PATH,
            )
            return None

        # Save token for next run
        with open(_TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    return build("calendar", "v3", credentials=creds)


# ── Real handlers ─────────────────────────────────────────────────────────

def _list_events_real(
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """List real Google Calendar events.

    Args:
        date: Single date (YYYY-MM-DD).
        date_from: Start of range (YYYY-MM-DD).
        date_to: End of range (YYYY-MM-DD).
        max_results: Max events to return.
    """
    service = _get_calendar_service()
    if not service:
        return [{"error": "Google Calendar not authenticated."}]

    # Determine time range
    if date:
        time_min = f"{date}T00:00:00"
        time_max = f"{date}T23:59:59"
    elif date_from and date_to:
        time_min = f"{date_from}T00:00:00"
        time_max = f"{date_to}T23:59:59"
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        time_min = f"{today}T00:00:00"
        time_max = f"{today}T23:59:59"

    try:
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=f"{time_min}+00:00",
                timeMax=f"{time_max}+00:00",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
    except Exception as exc:
        logger.exception("Google Calendar API error")
        return [{"error": f"Calendar API error: {exc}"}]

    results: list[dict[str, Any]] = []
    for event in events_result.get("items", []):
        start = event["start"].get("dateTime", event["start"].get("date", ""))
        end = event["end"].get("dateTime", event["end"].get("date", ""))

        # Extract time portion for display
        start_time = start.split("T")[1][:5] if "T" in start else "all-day"
        end_time = end.split("T")[1][:5] if "T" in end else "all-day"
        event_date = start.split("T")[0] if "T" in start else start

        results.append({
            "id": event["id"],
            "summary": event.get("summary", "(no title)"),
            "start": start_time,
            "end": end_time,
            "date": event_date,
            "description": event.get("description", ""),
            "location": event.get("location", ""),
        })

    logger.info("list_events (real): %d event(s)", len(results))
    return results


def _create_event_real(
    summary: str,
    start: str,
    end: str,
    date: str | None = None,
    description: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    """Create a real Google Calendar event."""
    service = _get_calendar_service()
    if not service:
        return {"error": "Google Calendar not authenticated."}

    event_date = date or datetime.now().strftime("%Y-%m-%d")

    event_body: dict[str, Any] = {
        "summary": summary,
        "start": {
            "dateTime": f"{event_date}T{start}:00",
            "timeZone": "Asia/Kuala_Lumpur",
        },
        "end": {
            "dateTime": f"{event_date}T{end}:00",
            "timeZone": "Asia/Kuala_Lumpur",
        },
    }

    if description:
        event_body["description"] = description
    if location:
        event_body["location"] = location

    try:
        created = (
            service.events()
            .insert(calendarId="primary", body=event_body)
            .execute()
        )
        logger.info("create_event (real): '%s' created (%s)", summary, created["id"])
        return {
            "id": created["id"],
            "summary": created.get("summary", summary),
            "start": start,
            "end": end,
            "date": event_date,
            "description": description,
            "location": location,
            "htmlLink": created.get("htmlLink", ""),
        }
    except Exception as exc:
        logger.exception("Failed to create event")
        return {"error": str(exc)}


def _update_event_real(
    event_id: str,
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    """Update a real Google Calendar event."""
    service = _get_calendar_service()
    if not service:
        return {"error": "Google Calendar not authenticated."}

    try:
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
    except Exception as exc:
        return {"error": f"Event not found: {exc}"}

    if summary:
        event["summary"] = summary
    if start and date:
        event["start"]["dateTime"] = f"{date}T{start}:00"
    if end and date:
        event["end"]["dateTime"] = f"{date}T{end}:00"

    try:
        updated = (
            service.events()
            .update(calendarId="primary", eventId=event_id, body=event)
            .execute()
        )
        logger.info("update_event (real): '%s' updated", event_id)
        return {
            "id": updated["id"],
            "summary": updated.get("summary", ""),
            "start": start or "",
            "end": end or "",
            "date": date or "",
            "htmlLink": updated.get("htmlLink", ""),
        }
    except Exception as exc:
        logger.exception("Failed to update event")
        return {"error": str(exc)}


def _delete_event_real(event_id: str) -> dict[str, Any]:
    """Delete a real Google Calendar event."""
    service = _get_calendar_service()
    if not service:
        return {"error": "Google Calendar not authenticated."}

    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        logger.info("delete_event (real): '%s' deleted", event_id)
        return {"deleted": True, "event_id": event_id}
    except Exception as exc:
        logger.exception("Failed to delete event")
        return {"error": str(exc)}


# ── Handler resolver ──────────────────────────────────────────────────────

def is_google_configured() -> bool:
    """Check if Google Calendar credentials are available."""
    return _CREDENTIALS_PATH.exists() or _TOKEN_PATH.exists()


def get_calendar_handlers() -> dict[str, Callable[..., Any]]:
    """Return the best available calendar tool handlers.

    Uses real Google Calendar API when credentials are available,
    falls back to mock data otherwise.

    Returns:
        Dict mapping tool name → handler function.
    """
    if is_google_configured():
        logger.info("Using REAL Google Calendar API.")
        return {
            "list_events": _list_events_real,
            "create_event": _create_event_real,
            "update_event": _update_event_real,
            "delete_event": _delete_event_real,
        }
    else:
        logger.info("Google not configured — using mock calendar data.")
        from agent.mcp.servers.calendar_server import (
            list_events,
            create_event,
            update_event,
            delete_event,
        )
        return {
            "list_events": list_events,
            "create_event": create_event,
            "update_event": update_event,
            "delete_event": delete_event,
        }
