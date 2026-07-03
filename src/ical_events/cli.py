"""Command-line interface for ical-events."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import __version__
from .calendar import collect_events, resolve_today
from .config import load_config
from .exceptions import DeployError, IcalEventsError
from .generator import generate_html, write_output


def run(argv: list[str] | None = None) -> None:
    """Parse arguments and generate the site. Raises IcalEventsError on failure."""
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
        "--today",
        help="Override the current date (YYYY-MM-DD) for reproducible builds; "
        "SOURCE_DATE_EPOCH is also honored",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args(argv)

    today = resolve_today(args.today)

    # Load config
    config = load_config(args.config)

    # Override output if specified
    if args.output:
        config.output.file = args.output

    # Fetch and parse all calendar sources
    events = collect_events(config, today)

    if not events:
        print(
            "Warning: No events found matching the configured filters.", file=sys.stderr
        )

    # Generate HTML
    html = generate_html(config, events)

    # Write output
    output_path = config.output.file
    write_output(html, output_path)
    print(f"Generated {len(events)} events → {output_path}")

    # Deploy to Cloudflare Pages if configured
    if config.wrangler_pages_project:
        output_dir = str(Path(output_path).parent)
        cmd = [
            "wrangler",
            "pages",
            "deploy",
            output_dir,
            f"--project-name={config.wrangler_pages_project}",
        ]
        print(f"Deploying to Cloudflare Pages project: {config.wrangler_pages_project}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise DeployError("wrangler pages deploy failed")


def main(argv: list[str] | None = None) -> None:
    try:
        run(argv)
    except IcalEventsError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(e.exit_code)
