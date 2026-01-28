"""Calendar fetching and event parsing."""

from __future__ import annotations

import hashlib
import sys
from datetime import date, datetime, timedelta

import requests
from ical.calendar_stream import IcsCalendarStream

from .models import FiltersConfig, TemplateEvent


def fetch_calendar_data(source: str) -> str:
    """Fetch ICS data from a URL or local file path."""
    if source.startswith("http://") or source.startswith("https://"):
        try:
            resp = requests.get(source, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"Error: Failed to fetch calendar from URL: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        from pathlib import Path

        path = Path(source)
        if not path.exists():
            print(f"Error: Calendar file not found: {source}", file=sys.stderr)
            sys.exit(2)
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"Error: Cannot read calendar file: {e}", file=sys.stderr)
            sys.exit(2)


def _make_anchor_id(uid: str) -> str:
    """Create a URL-safe anchor ID from a UID."""
    return hashlib.md5(uid.encode()).hexdigest()[:8]


def _format_date_display(start: date, end: date | None) -> str:
    """Format a human-readable date display string."""
    fmt = "%b %d, %Y"
    start_str = start.strftime(fmt)

    if end and end != start:
        if start.year == end.year and start.month == end.month:
            return f"{start.strftime('%b %d')}–{end.strftime('%d, %Y')}"
        elif start.year == end.year:
            return f"{start.strftime('%b %d')}–{end.strftime('%b %d, %Y')}"
        else:
            return f"{start_str}–{end.strftime(fmt)}"

    return start_str


def parse_events(ics_content: str, filters: FiltersConfig) -> list[TemplateEvent]:
    """Parse ICS content and return filtered, sorted TemplateEvent list."""
    try:
        calendars = IcsCalendarStream.calendar_from_ics(ics_content)
    except Exception as e:
        print(f"Error: Failed to parse calendar data: {e}", file=sys.stderr)
        sys.exit(2)

    start_filter = filters.start_date
    end_filter = filters.effective_end_date()

    events: list[TemplateEvent] = []

    for event in calendars.events:
        dtstart = event.dtstart
        dtend = event.dtend

        if dtstart is None:
            continue

        is_all_day = not isinstance(dtstart, datetime)

        if is_all_day:
            event_start_date = dtstart if isinstance(dtstart, date) else dtstart.date()
            if dtend:
                # ICS all-day end dates are exclusive — subtract 1 day for display
                event_end_raw = dtend if isinstance(dtend, date) else dtend.date()
                event_end_date = event_end_raw - timedelta(days=1)
            else:
                event_end_date = event_start_date

            start_dt = None
            end_dt = None
        else:
            event_start_date = dtstart.date()
            event_end_date = dtend.date() if dtend else event_start_date
            start_dt = dtstart
            end_dt = dtend

        # Apply date filters
        if event_start_date > end_filter:
            continue
        display_end = event_end_date if event_end_date else event_start_date
        if display_end < start_filter:
            continue

        duration = (display_end - event_start_date).days + 1

        uid = str(event.uid) if event.uid else ""
        categories_raw = event.categories or []
        categories = [str(c) for c in categories_raw]

        te = TemplateEvent(
            uid=uid,
            summary=str(event.summary) if event.summary else "Untitled Event",
            description=str(event.description) if event.description else None,
            location=str(event.location) if event.location else None,
            url=str(event.url) if event.url else None,
            start_date=event_start_date,
            end_date=event_end_date if event_end_date != event_start_date else None,
            start_datetime=start_dt,
            end_datetime=end_dt,
            is_all_day=is_all_day,
            categories=categories,
            month_key=event_start_date.strftime("%Y-%m"),
            anchor_id=_make_anchor_id(uid),
            date_display=_format_date_display(event_start_date, event_end_date if event_end_date != event_start_date else None),
            duration_days=duration,
        )
        events.append(te)

    # Sort chronologically
    events.sort(key=lambda e: (e.start_date, e.summary))

    # Apply max_events limit
    if filters.max_events is not None:
        events = events[: filters.max_events]

    return events
