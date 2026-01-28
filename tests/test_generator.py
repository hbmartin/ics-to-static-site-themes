"""Tests for HTML generation."""

from datetime import date

import pytest

from ical_events.calendar import parse_events
from ical_events.config import load_config
from ical_events.generator import generate_html
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
            date_display="Mar 15\u201317, 2026",
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


def test_full_pipeline(sample_config_path):
    """Integration test: config → parse → generate."""
    config = load_config(str(sample_config_path))
    filters = FiltersConfig(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    ics_path = config.calendar
    from pathlib import Path

    ics_content = Path(ics_path).read_text(encoding="utf-8")
    events = parse_events(ics_content, filters)
    html = generate_html(config, events)
    assert "<!DOCTYPE html>" in html
    assert len(events) > 0
