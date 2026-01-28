"""Tests for calendar parsing."""

from datetime import date

import pytest

from ical_events.calendar import parse_events, fetch_calendar_data
from ical_events.models import FiltersConfig


@pytest.fixture
def wide_filters():
    """Filters that include all test events (2024-2027)."""
    return FiltersConfig(start_date=date(2024, 1, 1), end_date=date(2027, 12, 31))


@pytest.fixture
def future_filters():
    """Filters that only include 2026+ events."""
    return FiltersConfig(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))


def test_parse_events_count(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters)
    # Should get 4 events (all-day, multi-day, no-url, april) — past event excluded
    assert len(events) == 4


def test_parse_events_all_day(sample_ics_content, wide_filters):
    events = parse_events(sample_ics_content, wide_filters)
    allday = [e for e in events if e.uid == "test-allday-1@test"]
    assert len(allday) == 1
    assert allday[0].is_all_day is True
    assert allday[0].start_date == date(2026, 3, 1)


def test_parse_events_multiday_exclusive_end(sample_ics_content, wide_filters):
    events = parse_events(sample_ics_content, wide_filters)
    multi = [e for e in events if e.uid == "test-multiday-2@test"]
    assert len(multi) == 1
    # DTEND is 20260313 (exclusive), so display end is March 12
    assert multi[0].end_date == date(2026, 3, 12)
    assert multi[0].duration_days == 3
    assert multi[0].url == "https://example.com/conference"


def test_parse_events_sorted(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters)
    dates = [e.start_date for e in events]
    assert dates == sorted(dates)


def test_parse_events_month_key(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters)
    month_keys = {e.month_key for e in events}
    assert "2026-03" in month_keys
    assert "2026-04" in month_keys


def test_parse_events_categories(sample_ics_content, wide_filters):
    events = parse_events(sample_ics_content, wide_filters)
    multi = [e for e in events if e.uid == "test-multiday-2@test"]
    assert "Conference" in multi[0].categories
    assert "Tech" in multi[0].categories


def test_parse_events_no_categories(sample_ics_content, wide_filters):
    events = parse_events(sample_ics_content, wide_filters)
    nourl = [e for e in events if e.uid == "test-nourl-3@test"]
    assert nourl[0].categories == []


def test_parse_events_max_events(sample_ics_content, future_filters):
    future_filters.max_events = 2
    events = parse_events(sample_ics_content, future_filters)
    assert len(events) == 2


def test_parse_events_filtering_excludes_past(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters)
    uids = {e.uid for e in events}
    assert "test-past-5@test" not in uids


def test_parse_events_anchor_id(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters)
    for event in events:
        assert len(event.anchor_id) == 8
        assert event.anchor_id.isalnum()


def test_fetch_calendar_data_file(sample_ics_path):
    content = fetch_calendar_data(str(sample_ics_path))
    assert "BEGIN:VCALENDAR" in content


def test_fetch_calendar_data_missing_file():
    with pytest.raises(SystemExit) as exc_info:
        fetch_calendar_data("/nonexistent/calendar.ics")
    assert exc_info.value.code == 2
