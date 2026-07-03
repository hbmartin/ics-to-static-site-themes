"""Tests for calendar parsing."""

from datetime import date
from zoneinfo import ZoneInfo

import pytest

from ical_events.calendar import (
    collect_events,
    fetch_calendar_data,
    parse_events,
    resolve_today,
)
from ical_events.exceptions import CalendarError
from ical_events.models import CategoryFilters, Config, FiltersConfig

TODAY = date(2026, 1, 1)


@pytest.fixture
def wide_filters():
    """Filters that include all test events (2024-2027)."""
    return FiltersConfig(start_date=date(2024, 1, 1), end_date=date(2027, 12, 31))


@pytest.fixture
def future_filters():
    """Filters that only include 2026+ events."""
    return FiltersConfig(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))


def test_parse_events_count(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters, today=TODAY)
    # Should get 4 events (all-day, multi-day, no-url, april) — past event excluded
    assert len(events) == 4


def test_parse_events_all_day(sample_ics_content, wide_filters):
    events = parse_events(sample_ics_content, wide_filters, today=TODAY)
    allday = [e for e in events if e.uid == "test-allday-1@test"]
    assert len(allday) == 1
    assert allday[0].is_all_day is True
    assert allday[0].start_date == date(2026, 3, 1)
    assert allday[0].time_display is None


def test_parse_events_multiday_exclusive_end(sample_ics_content, wide_filters):
    events = parse_events(sample_ics_content, wide_filters, today=TODAY)
    multi = [e for e in events if e.uid == "test-multiday-2@test"]
    assert len(multi) == 1
    # DTEND is 20260313 (exclusive), so display end is March 12
    assert multi[0].end_date == date(2026, 3, 12)
    assert multi[0].duration_days == 3
    assert multi[0].url == "https://example.com/conference"


def test_parse_events_sorted(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters, today=TODAY)
    dates = [e.start_date for e in events]
    assert dates == sorted(dates)


def test_parse_events_month_key(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters, today=TODAY)
    month_keys = {e.month_key for e in events}
    assert "2026-03" in month_keys
    assert "2026-04" in month_keys


def test_parse_events_categories(sample_ics_content, wide_filters):
    events = parse_events(sample_ics_content, wide_filters, today=TODAY)
    multi = [e for e in events if e.uid == "test-multiday-2@test"]
    assert "Conference" in multi[0].categories
    assert "Tech" in multi[0].categories


def test_parse_events_no_categories(sample_ics_content, wide_filters):
    events = parse_events(sample_ics_content, wide_filters, today=TODAY)
    nourl = [e for e in events if e.uid == "test-nourl-3@test"]
    assert nourl[0].categories == []


def test_parse_events_max_events(sample_ics_content, future_filters):
    future_filters.max_events = 2
    events = parse_events(sample_ics_content, future_filters, today=TODAY)
    assert len(events) == 2


def test_parse_events_filtering_excludes_past(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters, today=TODAY)
    uids = {e.uid for e in events}
    assert "test-past-5@test" not in uids


def test_parse_events_anchor_id(sample_ics_content, future_filters):
    events = parse_events(sample_ics_content, future_filters, today=TODAY)
    for event in events:
        assert len(event.anchor_id) == 8
        assert event.anchor_id.isalnum()


def test_parse_events_invalid_ics(future_filters):
    with pytest.raises(CalendarError):
        parse_events("not an ics file", future_filters, today=TODAY)


def test_parse_events_category_include(sample_ics_content, wide_filters):
    wide_filters.categories = CategoryFilters(include=["conference"])
    events = parse_events(sample_ics_content, wide_filters, today=TODAY)
    assert {e.uid for e in events} == {"test-multiday-2@test"}


def test_parse_events_category_exclude(sample_ics_content, wide_filters):
    wide_filters.categories = CategoryFilters(exclude=["Conference"])
    events = parse_events(sample_ics_content, wide_filters, today=TODAY)
    uids = {e.uid for e in events}
    assert "test-multiday-2@test" not in uids
    assert "test-allday-1@test" in uids


def test_parse_events_default_window(sample_ics_content):
    """With no explicit dates, events within a year of `today` are included."""
    filters = FiltersConfig()
    events = parse_events(sample_ics_content, filters, today=date(2026, 2, 1))
    uids = {e.uid for e in events}
    assert "test-allday-1@test" in uids
    assert "test-past-5@test" not in uids


# --- Recurrence expansion ---


def test_recurring_event_expanded(recurring_ics_content, future_filters):
    events = parse_events(recurring_ics_content, future_filters, today=TODAY)
    weekly = [e for e in events if e.uid == "weekly-meetup@test"]
    assert len(weekly) == 4
    starts = [e.start_date for e in weekly]
    assert starts == [
        date(2026, 1, 5),
        date(2026, 1, 12),
        date(2026, 1, 19),
        date(2026, 1, 26),
    ]


def test_recurring_instances_have_unique_ids(recurring_ics_content, future_filters):
    events = parse_events(recurring_ics_content, future_filters, today=TODAY)
    weekly = [e for e in events if e.uid == "weekly-meetup@test"]
    instance_ids = {e.instance_id for e in weekly}
    anchor_ids = {e.anchor_id for e in weekly}
    assert len(instance_ids) == 4
    assert len(anchor_ids) == 4


def test_recurring_window_limits_instances(recurring_ics_content):
    filters = FiltersConfig(start_date=date(2026, 1, 1), end_date=date(2026, 1, 14))
    events = parse_events(recurring_ics_content, filters, today=TODAY)
    weekly = [e for e in events if e.uid == "weekly-meetup@test"]
    assert len(weekly) == 2


# --- Timed events and timezones ---


def test_timed_event_has_time_display(recurring_ics_content, future_filters):
    events = parse_events(recurring_ics_content, future_filters, today=TODAY)
    weekly = [e for e in events if e.uid == "weekly-meetup@test"]
    assert weekly[0].is_all_day is False
    assert "6:00 PM" in weekly[0].time_display
    assert "8:00 PM" in weekly[0].time_display


def test_timed_event_timezone_conversion(recurring_ics_content, future_filters):
    la = ZoneInfo("America/Los_Angeles")
    events = parse_events(recurring_ics_content, future_filters, today=TODAY, tz=la)
    workshop = [e for e in events if e.uid == "timed-single@test"]
    # 9:00 AM Eastern == 6:00 AM Pacific
    assert workshop[0].start_datetime.hour == 6
    assert "6:00 AM" in workshop[0].time_display


# --- Fetching ---


def test_fetch_calendar_data_file(sample_ics_path):
    content = fetch_calendar_data(str(sample_ics_path))
    assert "BEGIN:VCALENDAR" in content


def test_fetch_calendar_data_missing_file():
    with pytest.raises(CalendarError):
        fetch_calendar_data("/nonexistent/calendar.ics")


# --- Multiple sources ---


def _make_config(sources, **kwargs) -> Config:
    return Config.model_validate(
        {
            "calendar": sources,
            "site": {"title": "T", "description": "D"},
            "filters": {"start_date": "2026-01-01", "end_date": "2026-12-31"},
            **kwargs,
        }
    )


def test_collect_events_single_source(sample_ics_path):
    config = _make_config(str(sample_ics_path))
    events = collect_events(config, TODAY)
    assert len(events) == 4
    assert all(e.source_label is None for e in events)


def test_collect_events_multiple_sources(sample_ics_path, recurring_ics_path):
    config = _make_config(
        [
            {"source": str(sample_ics_path), "label": "Sample", "color": "#ff0000"},
            {"source": str(recurring_ics_path), "label": "Recurring"},
        ]
    )
    events = collect_events(config, TODAY)
    labels = {e.source_label for e in events}
    assert labels == {"Sample", "Recurring"}
    sample_events = [e for e in events if e.source_label == "Sample"]
    assert sample_events[0].source_color == "#ff0000"
    # Merged result stays sorted
    dates = [e.start_date for e in events]
    assert dates == sorted(dates)


def test_collect_events_max_applied_after_merge(sample_ics_path, recurring_ics_path):
    config = _make_config([str(sample_ics_path), str(recurring_ics_path)])
    config.filters.max_events = 3
    events = collect_events(config, TODAY)
    assert len(events) == 3
    # The earliest events across both sources win (recurring starts in January)
    assert events[0].uid == "weekly-meetup@test"


# --- resolve_today ---


def test_resolve_today_override():
    assert resolve_today("2026-06-15") == date(2026, 6, 15)


def test_resolve_today_invalid_override():
    with pytest.raises(CalendarError):
        resolve_today("not-a-date")


def test_resolve_today_source_date_epoch(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1767225600")  # 2026-01-01 UTC
    assert resolve_today() == date(2026, 1, 1)


def test_resolve_today_invalid_epoch(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "garbage")
    with pytest.raises(CalendarError):
        resolve_today()


def test_resolve_today_default(monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    assert resolve_today() == date.today()
