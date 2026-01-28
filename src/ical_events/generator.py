"""HTML generation from parsed events and config."""

from __future__ import annotations

import json
import sys
from datetime import date
from itertools import groupby
from pathlib import Path

from jinja2 import Environment, PackageLoader, TemplateError

from .models import Config, TemplateEvent


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
            "startDate": event.start_date.isoformat(),
        }
        if event.end_date:
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
    """Generate the complete HTML page."""
    try:
        env = Environment(
            loader=PackageLoader("ical_events", "templates"),
            autoescape=True,
        )

        # Load CSS and JS as raw strings
        templates_dir = Path(__file__).parent / "templates"
        css_parts = []
        for css_file in ["styles/base.css", "styles/themes.css", "styles/components.css"]:
            css_parts.append(_load_template_file(templates_dir, css_file))
        inline_css = "\n".join(css_parts)

        js_parts = []
        for js_file in ["scripts/theme.js", "scripts/favorites.js", "scripts/filter.js"]:
            js_parts.append(_load_template_file(templates_dir, js_file))
        inline_js = "\n".join(js_parts)

        # Group events by month
        grouped = []
        for month_key, month_events_iter in groupby(events, key=lambda e: e.month_key):
            grouped.append((month_key, list(month_events_iter)))

        # Build JSON-LD
        jsonld = _build_jsonld(config, events)

        template = env.get_template("base.html.j2")
        html = template.render(
            config=config,
            events=events,
            grouped_events=grouped,
            month_label=_month_label,
            inline_css=inline_css,
            inline_js=inline_js,
            jsonld=jsonld,
        )
        return html

    except TemplateError as e:
        print(f"Error: Template rendering failed: {e}", file=sys.stderr)
        sys.exit(3)


def write_output(html: str, output_path: str) -> None:
    """Write the generated HTML to disk."""
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    except OSError as e:
        print(f"Error: Cannot write output file: {e}", file=sys.stderr)
        sys.exit(4)
