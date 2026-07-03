"""Calendar fetching and event parsing."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from ical.calendar_stream import IcsCalendarStream

from .exceptions import CalendarError
from .models import Config, FiltersConfig, TemplateEvent


def resolve_today(override: str | None = None) -> date:
    """Resolve the build's notion of "today".

    Precedence: explicit override (CLI --today), then SOURCE_DATE_EPOCH for
    reproducible builds, then the real current date.
    """
    if override:
        try:
            return date.fromisoformat(override)
        except ValueError as e:
            raise CalendarError(f"Invalid --today date: {override}") from e
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        try:
            return datetime.fromtimestamp(int(epoch), tz=UTC).date()
        except (ValueError, OverflowError, OSError) as e:
            raise CalendarError(f"Invalid SOURCE_DATE_EPOCH: {epoch}") from e
    return date.today()


def fetch_calendar_data(source: str) -> str:
    """Fetch ICS data from a URL or local file path.

    Raises CalendarError on failure.
    """
    if source.startswith("http://") or source.startswith("https://"):
        try:
            resp = requests.get(source, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            raise CalendarError(f"Failed to fetch calendar from URL: {e}") from e

    path = Path(source)
    if not path.exists():
        raise CalendarError(f"Calendar file not found: {source}")
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        raise CalendarError(f"Cannot read calendar file: {e}") from e


def _make_anchor_id(instance_id: str) -> str:
    """Create a URL-safe anchor ID from an event instance identifier."""
    return hashlib.md5(instance_id.encode()).hexdigest()[:8]


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


def _format_time(dt: datetime) -> str:
    """Format a time like '6:00 PM' without a leading zero."""
    return dt.strftime("%I:%M %p").lstrip("0")


def _format_time_display(start: datetime, end: datetime | None) -> str:
    """Format a human-readable time range for a timed event."""
    start_str = _format_time(start)
    if end and end != start:
        tz_abbr = start.strftime("%Z")
        suffix = f" {tz_abbr}" if tz_abbr else ""
        return f"{start_str}–{_format_time(end)}{suffix}"
    tz_abbr = start.strftime("%Z")
    return f"{start_str} {tz_abbr}".rstrip()


def parse_events(
    ics_content: str,
    filters: FiltersConfig,
    *,
    today: date | None = None,
    tz: ZoneInfo | None = None,
    source_label: str | None = None,
    source_color: str | None = None,
) -> list[TemplateEvent]:
    """Parse ICS content and return filtered, sorted TemplateEvent list.

    Recurring events (RRULE) are expanded into individual instances within
    the filter window. Timed events are converted to `tz` for display when
    provided. Raises CalendarError if the ICS data cannot be parsed.
    """
    if today is None:
        today = resolve_today()

    try:
        calendar = IcsCalendarStream.calendar_from_ics(ics_content)
    except Exception as e:
        raise CalendarError(f"Failed to parse calendar data: {e}") from e

    start_filter = filters.effective_start_date(today)
    end_filter = filters.effective_end_date(today)

    # Timeline expansion needs timezone-aware bounds; the end is exclusive.
    bounds_tz = tz or UTC
    range_start = datetime.combine(start_filter, time.min, tzinfo=bounds_tz)
    range_end = datetime.combine(
        end_filter + timedelta(days=1), time.min, tzinfo=bounds_tz
    )

    events: list[TemplateEvent] = []

    try:
        occurrences = list(calendar.timeline_tz(tz).overlapping(range_start, range_end))
    except Exception as e:
        raise CalendarError(f"Failed to expand calendar events: {e}") from e

    for event in occurrences:
        dtstart = event.dtstart
        dtend = event.dtend

        if dtstart is None:
            continue

        if not isinstance(dtstart, datetime):
            is_all_day = True
            event_start_date = dtstart
            if dtend:
                # ICS all-day end dates are exclusive — subtract 1 day for display
                event_end_raw = (
                    dtend if not isinstance(dtend, datetime) else dtend.date()
                )
                event_end_date = event_end_raw - timedelta(days=1)
            else:
                event_end_date = event_start_date

            start_dt = None
            end_dt = None
            time_display = None
        else:
            is_all_day = False
            start_dt = dtstart.astimezone(tz) if tz and dtstart.tzinfo else dtstart
            end_dt = dtend if isinstance(dtend, datetime) else None
            if end_dt is not None and tz and end_dt.tzinfo:
                end_dt = end_dt.astimezone(tz)
            event_start_date = start_dt.date()
            event_end_date = end_dt.date() if end_dt else event_start_date
            time_display = _format_time_display(start_dt, end_dt)

        display_end = event_end_date if event_end_date else event_start_date

        if not filters.categories.allows([str(c) for c in (event.categories or [])]):
            continue

        duration = (display_end - event_start_date).days + 1

        uid = str(event.uid) if event.uid else ""
        recurrence_id = getattr(event, "recurrence_id", None)
        instance_id = f"{uid}:{recurrence_id}" if recurrence_id else uid
        if not instance_id:
            # No UID at all — derive a stable identity from content
            instance_id = f"{event.summary}:{event_start_date.isoformat()}"
        categories = [str(c) for c in (event.categories or [])]

        te = TemplateEvent(
            uid=uid,
            instance_id=instance_id,
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
            anchor_id=_make_anchor_id(instance_id),
            date_display=_format_date_display(
                event_start_date,
                event_end_date if event_end_date != event_start_date else None,
            ),
            time_display=time_display,
            duration_days=duration,
            source_label=source_label,
            source_color=source_color,
        )
        events.append(te)

    _sort_events(events)

    if filters.max_events is not None:
        events = events[: filters.max_events]

    return events


def _sort_events(events: list[TemplateEvent]) -> None:
    """Sort events chronologically (all-day events first within a day)."""
    events.sort(
        key=lambda e: (
            e.start_date,
            e.start_datetime.timetz().isoformat() if e.start_datetime else "",
            e.summary,
        )
    )


def collect_events(config: Config, today: date) -> list[TemplateEvent]:
    """Fetch and parse all configured calendar sources, merged and sorted.

    max_events is applied to the merged result, not per source.
    """
    tz = config.tzinfo()
    per_source_filters = config.filters.model_copy(update={"max_events": None})

    events: list[TemplateEvent] = []
    for source in config.calendar_sources:
        ics_content = fetch_calendar_data(source.source)
        events.extend(
            parse_events(
                ics_content,
                per_source_filters,
                today=today,
                tz=tz,
                source_label=source.label,
                source_color=source.color,
            )
        )

    _sort_events(events)

    if config.filters.max_events is not None:
        events = events[: config.filters.max_events]

    return events
