# ical-events

A Python CLI that reads one or more ICS calendars (local or URL), applies a YAML configuration, and produces a single self-contained HTML page listing your events with switchable retro CSS themes.

- 7 retro visual themes (Windows 95, System 7, Y2K, Green Phosphor CRT, RedHat ncurses, Mr. Robot, Tron) selectable at runtime via theme bar
- Theme deep-linking (`?theme=tron`) and automatic dark-theme default for `prefers-color-scheme: dark` visitors
- Self-contained HTML output with all CSS and JavaScript inlined -- no external dependencies at runtime
- Recurring events (RRULE) are expanded into individual instances within the filter window
- Timed events display their start/end times, with optional timezone conversion via a `timezone` config option
- Multiple calendar sources with optional per-source labels and badge colors
- Event favoriting backed by `localStorage` with a heart toggle on each card
- Export favorited events as a downloadable `.ics` file
- Per-event "Add to Google Calendar" links and single-event `.ics` downloads
- Client-side search over event titles, descriptions, and locations
- Category filter chips in the page, plus config-side category include/exclude filters
- Copy-link buttons that copy a direct `#anchor` URL for any event to the clipboard
- Date filtering by start date, end date, and max event count
- "Show Favorites Only" toggle that filters the visible event list in place
- Events grouped by month with visual separators
- All-day and multi-day event support with correct handling of exclusive ICS end dates
- Event descriptions are safely rendered with clickable links and preserved line breaks
- SEO metadata: Open Graph, Twitter Cards, and JSON-LD structured data (organization + event list)
- Arbitrary custom `<meta>` tags via config
- Accessible markup: skip-link, ARIA roles/labels on all interactive controls, keyboard navigation, `prefers-reduced-motion` guards on animations
- Responsive layout that adapts from desktop to mobile
- Reproducible builds via `--today` or `SOURCE_DATE_EPOCH`
- Configurable via a single YAML file with sensible defaults
- Deterministic exit codes (1 = config error, 2 = calendar error, 3 = template error, 4 = write error, 5 = deploy error)

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```sh
git clone https://github.com/hbmartin/ics-to-static-site-themes
cd ics-to-static-site-themes
uv sync
```

## Quick Start

1. Create a YAML config file pointing at your calendar:

```yaml
calendar: example.ics

site:
  title: "LA Tech Events 2026"
  description: "Tech conferences and events in the LA area"

filters:
  start_date: "2026-01-01"
  end_date: "2026-12-31"

output:
  file: "./events/index.html"
```

2. Generate the HTML:

```sh
uv run ical-events config.yaml
```

3. Open `./events/index.html` in a browser.

## Usage

```
ical-events [-h] [-o OUTPUT] [--today TODAY] [--version] config
```

| Argument | Description |
|---|---|
| `config` | Path to the YAML configuration file |
| `-o`, `--output` | Override the output file path from the config |
| `--today` | Override the current date (`YYYY-MM-DD`) for reproducible builds; the `SOURCE_DATE_EPOCH` environment variable is also honored |
| `--version` | Print version and exit |

You can also run the tool as a Python module:

```sh
uv run python -m ical_events config.yaml
```

## Configuration Reference

```yaml
# One or more calendars: a local .ics path or a URL (required).
# A single string works, or a list for multiple sources — each entry may be
# a plain string or a mapping with an optional label and badge color.
calendar: ./my-calendar.ics
# calendar:
#   - ./local.ics
#   - source: https://example.com/remote.ics
#     label: "Remote"
#     color: "#88ccff"

# Site metadata (required)
site:
  title: "My Events"
  description: "Upcoming events"
  homepage_url: "https://example.com"   # optional, adds "Back to site" link
  x_username: "myhandle"                # optional, populates twitter:site meta tag

# IANA timezone for displaying timed events (optional).
# Timed events are converted to this zone; omit to keep each event's own zone.
timezone: "America/Los_Angeles"

# Date, count, and category filters (optional, defaults shown)
filters:
  start_date: null           # earliest event to include (default: today)
  end_date: null             # latest event to include (default: 1 year from today)
  max_events: null           # cap the number of events (default: unlimited)
  categories:
    include: []              # only keep events with at least one of these (case-insensitive)
    exclude: []              # drop events with any of these

# SEO and social metadata (optional)
meta:
  image: "https://example.com/og.png"   # og:image and twitter:image
  custom:                               # arbitrary <meta name="..." content="..."> tags
    author: "Your Name"

# JSON-LD structured data (optional)
structured_data:
  organization:
    name: "My Org"
    url: "https://example.com"
    logo: "https://example.com/logo.png"

# Output path (optional, default shown)
output:
  file: "./events/index.html"

# Optional: deploy the output directory to Cloudflare Pages after generation
# (requires the wrangler CLI to be installed and authenticated)
wrangler-pages-project: "my-project-name"
```

## Themes

All themes are applied via a `data-theme` attribute on `<body>` and use CSS custom properties, so switching is instant with no page reload. The selected theme is persisted in a cookie for one year and reflected in the URL as `?theme=...`, so a shared link opens in the same theme. Visitors with `prefers-color-scheme: dark` and no saved preference get the CRT theme by default.

| Theme | Visual Style |
|---|---|
| **Win 95** | Silver background, navy title bars, outset/inset borders |
| **System 7** | White background, black borders, offset drop shadows, pinstripe header |
| **Y2K** | Blue/cyan gradients, bubbly border-radius, gel buttons |
| **CRT** | Black background, green phosphor text with glow, scanline overlay |
| **ncurses** | Dark blue background, white/cyan text, TUI box-drawing borders, red buttons |
| **Mr. Robot** | Pure black, muted text, red accents, glitch hover effect |
| **Tron** | Dark blue-black, neon cyan glow borders, grid background |

## Deploying

The generated page is a single static HTML file, so it can be hosted anywhere.

- **GitHub Pages**: copy [`examples/deploy-github-pages.yml`](examples/deploy-github-pages.yml) into `.github/workflows/` to rebuild the page daily from your ICS URL and publish it via GitHub Pages.
- **Cloudflare Pages**: set `wrangler-pages-project` in your config and the CLI will run `wrangler pages deploy` on the output directory after generation.

## Exit Codes

| Code | Meaning |
|---|---|
| 1 | Configuration error (missing/invalid config file) |
| 2 | Calendar error (fetch, parse, or date-handling failure) |
| 3 | Template rendering error |
| 4 | Output write error |
| 5 | Deploy step failed |

## Development

```sh
uv sync --dev
uv run pytest             # tests with coverage (fails under 85%)
uv run ruff check .       # lint
uv run black --check .    # formatting
uv run ty check src       # type checking
```

## Project Structure

```
src/ical_events/
  __init__.py        # Package version
  __main__.py        # python -m entry point
  cli.py             # Argument parsing, orchestration, exit-code mapping
  config.py          # YAML loading and Pydantic validation
  calendar.py        # ICS fetching (file/URL), recurrence expansion, event parsing
  generator.py       # Jinja2 HTML rendering, calendar links, file output
  exceptions.py      # Typed errors mapped to exit codes
  models.py          # Pydantic data models
  templates/
    base.html.j2     # Master HTML template
    components/      # Event card, theme bar, filter bar, month separator
    styles/          # base.css, themes.css, components.css
    scripts/         # theme.js, favorites.js, filter.js
tests/
  test_config.py     # Config loading and validation tests
  test_calendar.py   # ICS parsing, recurrence, and filtering tests
  test_generator.py  # HTML generation and integration tests
  test_cli.py        # CLI behavior and exit-code tests
  fixtures/          # Sample .ics and config files
examples/
  deploy-github-pages.yml  # Scheduled rebuild + GitHub Pages deploy workflow
```

## License

See [LICENSE.txt](LICENSE.txt) for details.
