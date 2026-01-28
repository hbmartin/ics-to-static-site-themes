"""Command-line interface for ical-events."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .calendar import fetch_calendar_data, parse_events
from .config import load_config
from .generator import generate_html, write_output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="ical-events",
        description="Generate a static HTML event listing from an ICS calendar",
    )
    parser.add_argument("config", help="Path to YAML configuration file")
    parser.add_argument(
        "-o",
        "--output",
        help="Override output file path",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args(argv)

    # Load config
    config = load_config(args.config)

    # Override output if specified
    if args.output:
        config.output.file = args.output

    # Fetch and parse calendar
    ics_content = fetch_calendar_data(config.calendar)
    events = parse_events(ics_content, config.filters)

    if not events:
        print("Warning: No events found matching the configured filters.", file=sys.stderr)

    # Generate HTML
    html = generate_html(config, events)

    # Write output
    output_path = config.output.file
    write_output(html, output_path)
    print(f"Generated {len(events)} events → {output_path}")
