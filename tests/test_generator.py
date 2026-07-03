"""Tests for HTML generation."""

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from ical_events.calendar import parse_events
from ical_events.config import load_config
from ical_events.generator import (
    event_to_ics,
    generate_html,
    google_calendar_url,
    render_description,
    write_output,
)
from ical_events.models import Config, FiltersConfig, SiteConfig, TemplateEvent


@pytest.fixture
def minimal_config():
    return Config(
        calendar="test.ics",
        site=SiteConfig(
            title="Test Events",
            description="A test listing",
            homepage_url="https://example.com",
            x_username="testuser",
        ),
    )


@pytest.fixture
def sample_events():
    return [
        TemplateEvent(
            uid="ev1",
            summary="First Event",
            description="Description of first event",
            location="Los Angeles, CA",
            url="https://example.com/event1",
            start_date=date(2026, 3, 1),
            is_all_day=True,
            categories=["Tech", "AI"],
            month_key="2026-03",
            anchor_id="abcd1234",
            date_display="Mar 01, 2026",
            duration_days=1,
        ),
        TemplateEvent(
            uid="ev2",
            summary="Second Event",
            start_date=date(2026, 3, 15),
            end_date=date(2026, 3, 17),
            is_all_day=True,
            month_key="2026-03",
            anchor_id="efgh5678",
            date_display="Mar 15–17, 2026",
            duration_days=3,
        ),
        TemplateEvent(
            uid="ev3",
            summary="April Event",
            start_date=date(2026, 4, 1),
            is_all_day=True,
            month_key="2026-04",
            anchor_id="ijkl9012",
            date_display="Apr 01, 2026",
            duration_days=1,
        ),
    ]


def test_generate_html_structure(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "<!DOCTYPE html>" in html
    assert "<html lang=" in html
    assert "</html>" in html


def test_generate_html_title(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "<title>Test Events</title>" in html


def test_generate_html_meta_tags(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "og:title" in html
    assert "og:description" in html
    assert "twitter:card" in html
    assert "@testuser" in html


def test_generate_html_inline_css(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "<style>" in html
    assert "data-theme" in html
    assert "win95" in html


def test_generate_html_inline_js(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "<script>" in html
    assert "events-theme" in html
    assert "events-favorites" in html


def test_generate_html_events(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "First Event" in html
    assert "Second Event" in html
    assert "April Event" in html


def test_generate_html_event_cards(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert 'class="event-card"' in html
    assert 'data-uid="ev1"' in html


def test_generate_html_month_separators(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "March 2026" in html
    assert "April 2026" in html


def test_generate_html_event_url(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert 'href="https://example.com/event1"' in html


def test_generate_html_categories(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "Tech" in html
    assert "AI" in html


def test_generate_html_category_chips(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert 'class="category-chip"' in html
    assert 'data-category="tech"' in html
    assert 'data-category="ai"' in html
    assert 'data-categories="tech||ai"' in html


def test_generate_html_search_input(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert 'class="search-input"' in html


def test_generate_html_add_to_calendar(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "calendar.google.com/calendar/render" in html
    assert "data:text/calendar" in html
    assert 'download="abcd1234.ics"' in html


def test_generate_html_export_data(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert 'id="event-export-data"' in html
    start = html.index('id="event-export-data">') + len('id="event-export-data">')
    end = html.index("</script>", start)
    payload = json.loads(html[start:end])
    assert {entry["id"] for entry in payload} == {"ev1", "ev2", "ev3"}
    assert all("BEGIN:VEVENT" in entry["ics"] for entry in payload)


def test_generate_html_accessibility(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert 'class="skip-link"' in html
    assert "aria-label" in html
    assert "aria-pressed" in html
    assert "aria-checked" in html


def test_generate_html_jsonld(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "application/ld+json" in html
    assert "schema.org" in html


def test_generate_html_theme_buttons(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    for theme in ["win95", "system7", "y2k", "phosphor", "redhat", "mr-robot", "tron"]:
        assert f'data-theme-value="{theme}"' in html


def test_generate_html_copy_link(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert 'class="action-btn copy-btn"' in html
    assert 'data-anchor="abcd1234"' in html


def test_generate_html_favorite_button(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert 'class="action-btn favorite-btn"' in html


def test_generate_html_homepage_link(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert 'href="https://example.com"' in html
    assert "Back to site" in html


def test_generate_html_filter_bar(minimal_config, sample_events):
    html = generate_html(minimal_config, sample_events)
    assert "3 events" in html
    assert "Favorites Only" in html
    assert "Export Favorites" in html


def test_generate_html_source_badge(minimal_config, sample_events):
    sample_events[0].source_label = "Main Cal"
    sample_events[0].source_color = "#ff0000"
    html = generate_html(minimal_config, sample_events)
    assert 'class="source-badge"' in html
    assert "Main Cal" in html
    assert "--source-color: #ff0000" in html


def test_generate_html_time_display(minimal_config, sample_events):
    sample_events[0].is_all_day = False
    sample_events[0].time_display = "6:00 PM–8:00 PM PST"
    html = generate_html(minimal_config, sample_events)
    assert "6:00 PM–8:00 PM PST" in html


# --- render_description ---


def test_render_description_escapes_html():
    result = str(render_description("<script>alert(1)</script>"))
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_render_description_linkifies_urls():
    result = str(render_description("See https://example.com/page for info"))
    assert '<a href="https://example.com/page"' in result
    assert 'rel="noopener noreferrer"' in result


def test_render_description_strips_trailing_punctuation_from_links():
    result = str(render_description("Visit https://example.com."))
    assert '<a href="https://example.com"' in result


def test_render_description_newlines():
    result = str(render_description("line one\nline two"))
    assert "<br>" in result


def test_render_description_literal_backslash_n():
    result = str(render_description("line one\\nline two"))
    assert "<br>" in result


def test_render_description_in_page(minimal_config, sample_events):
    sample_events[0].description = "Details: https://tickets.example.com\nBe there!"
    html = generate_html(minimal_config, sample_events)
    assert '<a href="https://tickets.example.com"' in html
    assert "<br>" in html


# --- Google Calendar URLs ---


def test_google_calendar_url_all_day():
    event = TemplateEvent(
        uid="e1",
        summary="Party",
        start_date=date(2026, 3, 1),
        location="LA",
    )
    url = google_calendar_url(event)
    assert "action=TEMPLATE" in url
    assert "text=Party" in url
    # All-day: exclusive end date is the next day
    assert "dates=20260301%2F20260302" in url
    assert "location=LA" in url


def test_google_calendar_url_multi_day():
    event = TemplateEvent(
        uid="e2",
        summary="Conf",
        start_date=date(2026, 3, 10),
        end_date=date(2026, 3, 12),
    )
    url = google_calendar_url(event)
    assert "dates=20260310%2F20260313" in url


def test_google_calendar_url_timed():
    event = TemplateEvent(
        uid="e3",
        summary="Meeting",
        start_date=date(2026, 3, 1),
        start_datetime=datetime(2026, 3, 1, 18, 0, tzinfo=UTC),
        end_datetime=datetime(2026, 3, 1, 20, 0, tzinfo=UTC),
        is_all_day=False,
    )
    url = google_calendar_url(event)
    assert "dates=20260301T180000Z%2F20260301T200000Z" in url


# --- Per-event ICS ---


def test_event_to_ics_all_day():
    event = TemplateEvent(
        uid="e1",
        summary="Party; fun, right?",
        start_date=date(2026, 3, 1),
        description="Line one\nline two",
    )
    ics = event_to_ics(event)
    assert "BEGIN:VCALENDAR" in ics
    assert "DTSTART;VALUE=DATE:20260301" in ics
    assert "DTEND;VALUE=DATE:20260302" in ics
    assert "SUMMARY:Party\\; fun\\, right?" in ics
    assert "DESCRIPTION:Line one\\nline two" in ics


def test_event_to_ics_timed():
    event = TemplateEvent(
        uid="e2",
        summary="Meeting",
        start_date=date(2026, 3, 1),
        start_datetime=datetime(2026, 3, 1, 18, 0, tzinfo=UTC),
        end_datetime=datetime(2026, 3, 1, 20, 0, tzinfo=UTC),
        is_all_day=False,
    )
    ics = event_to_ics(event)
    assert "DTSTART:20260301T180000Z" in ics
    assert "DTEND:20260301T200000Z" in ics


# --- JSON-LD ---


def test_jsonld_uses_datetime_when_available(minimal_config, sample_events):
    sample_events[0].is_all_day = False
    sample_events[0].start_datetime = datetime(2026, 3, 1, 18, 0, tzinfo=UTC)
    html = generate_html(minimal_config, sample_events)
    assert "2026-03-01T18:00:00+00:00" in html


# --- write_output ---


def test_write_output_creates_dirs(tmp_path):
    out = tmp_path / "nested" / "dir" / "index.html"
    write_output("<html></html>", str(out))
    assert out.read_text() == "<html></html>"


def test_full_pipeline(sample_config_path):
    """Integration test: config → parse → generate."""
    config = load_config(str(sample_config_path))
    filters = FiltersConfig(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    ics_content = Path(config.calendar_sources[0].source).read_text(encoding="utf-8")
    events = parse_events(ics_content, filters, today=date(2026, 1, 1))
    html = generate_html(config, events)
    assert "<!DOCTYPE html>" in html
    assert len(events) > 0
