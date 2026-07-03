"""HTML generation from parsed events and config."""

from __future__ import annotations

import json
import re
from datetime import UTC, date, timedelta
from itertools import groupby
from pathlib import Path
from urllib.parse import quote, urlencode

from jinja2 import Environment, PackageLoader, TemplateError
from markupsafe import Markup, escape

from .exceptions import OutputWriteError, TemplateRenderError
from .models import Config, TemplateEvent

_URL_RE = re.compile(r"https?://[^\s<>\"']+")


def render_description(text: str) -> Markup:
    """Render an event description as safe HTML.

    Escapes all markup, converts literal "\\n" sequences and real newlines
    to <br>, and linkifies bare URLs.
    """
    normalized = text.replace("\\n", "\n")

    parts: list[str] = []
    pos = 0
    for match in _URL_RE.finditer(normalized):
        parts.append(str(escape(normalized[pos : match.start()])))
        url = match.group(0).rstrip(".,;:!?)")
        trailing = match.group(0)[len(url) :]
        parts.append(
            f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">'
            f"{escape(url)}</a>{escape(trailing)}"
        )
        pos = match.end()
    parts.append(str(escape(normalized[pos:])))

    html = "".join(parts).replace("\n", "<br>\n")
    return Markup(html)


def _gcal_dates(event: TemplateEvent) -> str:
    """Format the dates parameter for a Google Calendar template URL."""
    if event.is_all_day or not event.start_datetime:
        start = event.start_date
        # Google expects an exclusive end date for all-day events
        end = (event.end_date or event.start_date) + timedelta(days=1)
        return f"{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"

    start_dt = event.start_datetime
    end_dt = event.end_datetime or start_dt
    if start_dt.tzinfo:
        start_dt = start_dt.astimezone(UTC)
        end_dt = end_dt.astimezone(UTC)
        fmt = "%Y%m%dT%H%M%SZ"
    else:
        fmt = "%Y%m%dT%H%M%S"
    return f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"


def google_calendar_url(event: TemplateEvent) -> str:
    """Build an 'add to Google Calendar' template URL for an event."""
    params: dict[str, str] = {
        "action": "TEMPLATE",
        "text": event.summary,
        "dates": _gcal_dates(event),
    }
    if event.description:
        params["details"] = event.description
    if event.location:
        params["location"] = event.location
    return "https://calendar.google.com/calendar/render?" + urlencode(params)


def _ics_escape(value: str) -> str:
    """Escape a text value per RFC 5545."""
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def event_to_ics(event: TemplateEvent) -> str:
    """Serialize a single event as a minimal standalone VCALENDAR."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ical-events//EN",
        "BEGIN:VEVENT",
        f"UID:{_ics_escape(event.instance_id or event.uid)}",
        f"SUMMARY:{_ics_escape(event.summary)}",
    ]
    if event.is_all_day or not event.start_datetime:
        end = (event.end_date or event.start_date) + timedelta(days=1)
        lines.append(f"DTSTART;VALUE=DATE:{event.start_date.strftime('%Y%m%d')}")
        lines.append(f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}")
    else:
        start_dt = event.start_datetime
        end_dt = event.end_datetime or start_dt
        if start_dt.tzinfo:
            start_dt = start_dt.astimezone(UTC)
            end_dt = end_dt.astimezone(UTC)
            fmt = "%Y%m%dT%H%M%SZ"
        else:
            fmt = "%Y%m%dT%H%M%S"
        lines.append(f"DTSTART:{start_dt.strftime(fmt)}")
        lines.append(f"DTEND:{end_dt.strftime(fmt)}")
    if event.description:
        lines.append(f"DESCRIPTION:{_ics_escape(event.description)}")
    if event.location:
        lines.append(f"LOCATION:{_ics_escape(event.location)}")
    if event.url:
        lines.append(f"URL:{event.url}")
    lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def event_ics_data_uri(event: TemplateEvent) -> str:
    """Build a data: URI holding a downloadable .ics file for one event."""
    return "data:text/calendar;charset=utf-8," + quote(event_to_ics(event))


def _event_export_data(events: list[TemplateEvent]) -> str:
    """JSON blob embedded in the page so favorites can be exported as .ics."""
    payload = [
        {"id": event.instance_id, "ics": event_to_ics(event)} for event in events
    ]
    # Avoid closing the surrounding <script> tag early
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def _build_jsonld(config: Config, events: list[TemplateEvent]) -> str:
    """Build JSON-LD structured data for the page."""
    data: dict = {"@context": "https://schema.org"}

    items: list[dict] = []

    # Organization
    if config.structured_data.organization:
        org = config.structured_data.organization
        org_data: dict = {
            "@type": "Organization",
            "name": org.name,
            "url": org.url,
        }
        if org.logo:
            org_data["logo"] = org.logo
        items.append(org_data)

    # Events
    for event in events:
        ev: dict = {
            "@type": "Event",
            "name": event.summary,
            "startDate": (
                event.start_datetime.isoformat()
                if event.start_datetime
                else event.start_date.isoformat()
            ),
        }
        if event.end_datetime:
            ev["endDate"] = event.end_datetime.isoformat()
        elif event.end_date:
            ev["endDate"] = event.end_date.isoformat()
        if event.description:
            ev["description"] = event.description
        if event.location:
            ev["location"] = {
                "@type": "Place",
                "name": event.location,
            }
        if event.url:
            ev["url"] = event.url
        items.append(ev)

    if len(items) == 1:
        data.update(items[0])
    elif len(items) > 1:
        data["@graph"] = items

    return json.dumps(data, indent=2, ensure_ascii=False)


def _load_template_file(base_path: Path, *parts: str) -> str:
    """Read a template file from disk."""
    path = base_path.joinpath(*parts)
    return path.read_text(encoding="utf-8")


def _month_label(month_key: str) -> str:
    """Convert a YYYY-MM key to a human-readable month label."""
    try:
        year, month = month_key.split("-")
        d = date(int(year), int(month), 1)
        return d.strftime("%B %Y")
    except (ValueError, IndexError):
        return month_key


def generate_html(config: Config, events: list[TemplateEvent]) -> str:
    """Generate the complete HTML page.

    Raises TemplateRenderError if rendering fails.
    """
    try:
        env = Environment(
            loader=PackageLoader("ical_events", "templates"),
            autoescape=True,
        )
        env.filters["render_description"] = render_description
        env.filters["gcal_url"] = google_calendar_url
        env.filters["ics_data_uri"] = event_ics_data_uri

        # Load CSS and JS as raw strings
        templates_dir = Path(__file__).parent / "templates"
        css_parts = []
        for css_file in [
            "styles/base.css",
            "styles/themes.css",
            "styles/components.css",
        ]:
            css_parts.append(_load_template_file(templates_dir, css_file))
        inline_css = "\n".join(css_parts)

        js_parts = []
        for js_file in [
            "scripts/theme.js",
            "scripts/favorites.js",
            "scripts/filter.js",
        ]:
            js_parts.append(_load_template_file(templates_dir, js_file))
        inline_js = "\n".join(js_parts)

        # Group events by month
        grouped = []
        for month_key, month_events_iter in groupby(events, key=lambda e: e.month_key):
            grouped.append((month_key, list(month_events_iter)))

        # Unique categories across all events, for the filter chips
        all_categories = sorted(
            {cat for event in events for cat in event.categories},
            key=str.lower,
        )

        # Build JSON-LD
        jsonld = _build_jsonld(config, events)

        template = env.get_template("base.html.j2")
        html = template.render(
            config=config,
            events=events,
            grouped_events=grouped,
            all_categories=all_categories,
            month_label=_month_label,
            inline_css=inline_css,
            inline_js=inline_js,
            jsonld=jsonld,
            event_export_data=_event_export_data(events),
        )
        return html

    except TemplateError as e:
        raise TemplateRenderError(f"Template rendering failed: {e}") from e


def write_output(html: str, output_path: str) -> None:
    """Write the generated HTML to disk.

    Raises OutputWriteError on failure.
    """
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    except OSError as e:
        raise OutputWriteError(f"Cannot write output file: {e}") from e
