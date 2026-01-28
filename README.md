# ical-events

A Python CLI that reads an ICS calendar file (local or URL), applies a YAML configuration, and produces a single self-contained HTML page listing your events with switchable retro CSS themes.

- 7 retro visual themes (Windows 95, System 7, Y2K, Green Phosphor CRT, RedHat ncurses, Mr. Robot, Tron) selectable at runtime via theme bar
- Self-contained HTML output with all CSS and JavaScript inlined -- no external dependencies at runtime
- Event favoriting backed by `localStorage` with a heart toggle on each card
- Copy-link buttons that copy a direct `#anchor` URL for any event to the clipboard
- Date filtering by start date, end date, and max event count
- "Show Favorites Only" toggle that filters the visible event list in place
- Events grouped by month with visual separators
- All-day and multi-day event support with correct handling of exclusive ICS end dates
- SEO metadata: Open Graph, Twitter Cards, and JSON-LD structured data (organization + event list)
- Arbitrary custom `<meta>` tags via config
- Accessible markup: skip-link, ARIA roles/labels on all interactive controls, keyboard navigation, `prefers-reduced-motion` guards on animations
- Responsive layout that adapts from desktop to mobile
- Calendar source can be a local `.ics` file path or a remote URL
- Configurable via a single YAML file with sensible defaults
- Deterministic exit codes (1 = config error, 2 = calendar error, 3 = template error, 4 = write error)

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```sh
git clone <repo-url>
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
ical-events [-h] [-o OUTPUT] [--version] config
```

| Argument | Description |
|---|---|
| `config` | Path to the YAML configuration file |
| `-o`, `--output` | Override the output file path from the config |
| `--version` | Print version and exit |

You can also run the tool as a Python module:

```sh
uv run python -m ical_events config.yaml
```

## Configuration Reference

```yaml
# Path to a local .ics file or a URL (required)
calendar: ./my-calendar.ics

# Site metadata (required)
site:
  title: "My Events"
  description: "Upcoming events"
  homepage_url: "https://example.com"   # optional, adds "Back to site" link
  x_username: "myhandle"                # optional, populates twitter:site meta tag

# Date and count filters (optional, defaults shown)
filters:
  start_date: today          # earliest event to include (default: today)
  end_date: null             # latest event to include (default: 1 year from today)
  max_events: null           # cap the number of events (default: unlimited)

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
```

## Themes

All themes are applied via a `data-theme` attribute on `<body>` and use CSS custom properties, so switching is instant with no page reload. The selected theme is persisted in a cookie for one year.

| Theme | Visual Style |
|---|---|
| **Win 95** | Silver background, navy title bars, outset/inset borders |
| **System 7** | White background, black borders, offset drop shadows, pinstripe header |
| **Y2K** | Blue/cyan gradients, bubbly border-radius, gel buttons |
| **CRT** | Black background, green phosphor text with glow, scanline overlay |
| **ncurses** | Dark blue background, white/cyan text, TUI box-drawing borders, red buttons |
| **Mr. Robot** | Pure black, muted text, red accents, glitch hover effect |
| **Tron** | Dark blue-black, neon cyan glow borders, grid background |

## Running Tests

```sh
uv run pytest tests/ -v
```

## Project Structure

```
src/ical_events/
  __init__.py        # Package version
  __main__.py        # python -m entry point
  cli.py             # Argument parsing and orchestration
  config.py          # YAML loading and Pydantic validation
  calendar.py        # ICS fetching (file/URL) and event parsing
  generator.py       # Jinja2 HTML rendering and file output
  models.py          # Pydantic data models
  templates/
    base.html.j2     # Master HTML template
    components/      # Event card, theme bar, filter bar, month separator
    styles/          # base.css, themes.css, components.css
    scripts/         # theme.js, favorites.js, filter.js
tests/
  test_config.py     # Config loading and validation tests
  test_calendar.py   # ICS parsing and filtering tests
  test_generator.py  # HTML generation and integration tests
  fixtures/          # Sample .ics and config files
```

## License

See [LICENSE](LICENSE) for details.
