"""Tests for config loading and validation."""

import textwrap

import pytest

from ical_events.config import load_config


def test_load_valid_config(sample_config_path):
    config = load_config(str(sample_config_path))
    assert config.site.title == "Test Events"
    assert config.site.description == "A test event listing"
    assert config.site.homepage_url == "https://example.com"
    assert config.site.x_username == "testuser"
    assert config.calendar == "tests/fixtures/sample.ics"
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
    assert config.meta.image is None
    assert config.structured_data.organization is None


def test_config_missing_file():
    with pytest.raises(SystemExit) as exc_info:
        load_config("/nonexistent/path/config.yaml")
    assert exc_info.value.code == 1


def test_config_invalid_yaml(tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text(":::invalid yaml:::")
    with pytest.raises(SystemExit) as exc_info:
        load_config(str(cfg))
    assert exc_info.value.code == 1


def test_config_missing_required_fields(tmp_path):
    cfg = tmp_path / "incomplete.yaml"
    cfg.write_text("calendar: test.ics\n")
    with pytest.raises(SystemExit) as exc_info:
        load_config(str(cfg))
    assert exc_info.value.code == 1


def test_config_not_a_mapping(tmp_path):
    cfg = tmp_path / "list.yaml"
    cfg.write_text("- item1\n- item2\n")
    with pytest.raises(SystemExit) as exc_info:
        load_config(str(cfg))
    assert exc_info.value.code == 1
