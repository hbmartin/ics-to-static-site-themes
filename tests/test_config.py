"""Tests for config loading and validation."""

import textwrap

import pytest

from ical_events.config import load_config
from ical_events.exceptions import ConfigError


def test_load_valid_config(sample_config_path):
    config = load_config(str(sample_config_path))
    assert config.site.title == "Test Events"
    assert config.site.description == "A test event listing"
    assert config.site.homepage_url == "https://example.com"
    assert config.site.x_username == "testuser"
    assert config.calendar_sources[0].source == "tests/fixtures/sample.ics"
    assert config.meta.image == "https://example.com/og-image.png"
    assert config.meta.custom["author"] == "Test Author"
    assert config.structured_data.organization is not None
    assert config.structured_data.organization.name == "Test Org"


def test_config_defaults(tmp_path):
    cfg = tmp_path / "minimal.yaml"
    cfg.write_text(textwrap.dedent("""\
        calendar: test.ics
        site:
          title: Minimal
          description: Minimal test
    """))
    config = load_config(str(cfg))
    assert config.output.file == "./events/index.html"
    assert config.filters.max_events is None
    assert config.filters.start_date is None
    assert config.meta.image is None
    assert config.structured_data.organization is None
    assert config.timezone is None
    assert config.tzinfo() is None


def test_config_multiple_calendars(tmp_path):
    cfg = tmp_path / "multi.yaml"
    cfg.write_text(textwrap.dedent("""\
        calendar:
          - one.ics
          - source: two.ics
            label: Second
            color: "#00ff00"
        site:
          title: Multi
          description: Multi test
    """))
    config = load_config(str(cfg))
    sources = config.calendar_sources
    assert len(sources) == 2
    assert sources[0].source == "one.ics"
    assert sources[0].label is None
    assert sources[1].source == "two.ics"
    assert sources[1].label == "Second"
    assert sources[1].color == "#00ff00"


def test_config_timezone(tmp_path):
    cfg = tmp_path / "tz.yaml"
    cfg.write_text(textwrap.dedent("""\
        calendar: test.ics
        timezone: America/Los_Angeles
        site:
          title: TZ
          description: TZ test
    """))
    config = load_config(str(cfg))
    assert config.timezone == "America/Los_Angeles"
    assert str(config.tzinfo()) == "America/Los_Angeles"


def test_config_invalid_timezone(tmp_path):
    cfg = tmp_path / "badtz.yaml"
    cfg.write_text(textwrap.dedent("""\
        calendar: test.ics
        timezone: Not/AZone
        site:
          title: TZ
          description: TZ test
    """))
    with pytest.raises(ConfigError):
        load_config(str(cfg))


def test_config_category_filters(tmp_path):
    cfg = tmp_path / "cats.yaml"
    cfg.write_text(textwrap.dedent("""\
        calendar: test.ics
        site:
          title: Cats
          description: Cats test
        filters:
          categories:
            include: [Tech, Conference]
            exclude: [Cancelled]
    """))
    config = load_config(str(cfg))
    cats = config.filters.categories
    assert cats.allows(["tech"])
    assert not cats.allows(["Music"])
    assert not cats.allows(["Tech", "Cancelled"])
    assert cats.allows(["Conference", "Other"])


def test_config_missing_file():
    with pytest.raises(ConfigError):
        load_config("/nonexistent/path/config.yaml")


def test_config_invalid_yaml(tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text(":::invalid yaml:::")
    with pytest.raises(ConfigError):
        load_config(str(cfg))


def test_config_missing_required_fields(tmp_path):
    cfg = tmp_path / "incomplete.yaml"
    cfg.write_text("calendar: test.ics\n")
    with pytest.raises(ConfigError):
        load_config(str(cfg))


def test_config_not_a_mapping(tmp_path):
    cfg = tmp_path / "list.yaml"
    cfg.write_text("- item1\n- item2\n")
    with pytest.raises(ConfigError):
        load_config(str(cfg))
