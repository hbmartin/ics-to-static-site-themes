"""Tests for the command-line interface."""

import textwrap

import pytest

from ical_events.cli import main

FIXTURE_ICS = "tests/fixtures/sample.ics"


def _write_config(tmp_path, ics_path, **extra_lines):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""\
        calendar: {ics_path}
        site:
          title: CLI Test
          description: CLI test listing
        filters:
          start_date: "2026-01-01"
          end_date: "2026-12-31"
        output:
          file: {tmp_path / "out" / "index.html"}
    """))
    return cfg


def test_cli_generates_output(tmp_path, sample_ics_path, capsys):
    cfg = _write_config(tmp_path, sample_ics_path)
    main([str(cfg)])
    out_file = tmp_path / "out" / "index.html"
    assert out_file.exists()
    assert "<!DOCTYPE html>" in out_file.read_text()
    captured = capsys.readouterr()
    assert "Generated 4 events" in captured.out


def test_cli_output_override(tmp_path, sample_ics_path):
    cfg = _write_config(tmp_path, sample_ics_path)
    override = tmp_path / "custom.html"
    main([str(cfg), "-o", str(override)])
    assert override.exists()


def test_cli_today_override(tmp_path, sample_ics_path, capsys):
    """--today plus default filters gives a deterministic window."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""\
        calendar: {sample_ics_path}
        site:
          title: CLI Test
          description: CLI test listing
        output:
          file: {tmp_path / "out" / "index.html"}
    """))
    main([str(cfg), "--today", "2026-02-01"])
    captured = capsys.readouterr()
    assert "Generated 4 events" in captured.out


def test_cli_missing_config_exit_code(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "missing.yaml")])
    assert exc_info.value.code == 1


def test_cli_missing_calendar_exit_code(tmp_path):
    cfg = _write_config(tmp_path, "/nonexistent/calendar.ics")
    with pytest.raises(SystemExit) as exc_info:
        main([str(cfg)])
    assert exc_info.value.code == 2


def test_cli_invalid_today_exit_code(tmp_path, sample_ics_path):
    cfg = _write_config(tmp_path, sample_ics_path)
    with pytest.raises(SystemExit) as exc_info:
        main([str(cfg), "--today", "bogus"])
    assert exc_info.value.code == 2
