"""Typed exceptions mapped to CLI exit codes."""

from __future__ import annotations


class IcalEventsError(Exception):
    """Base class for all ical-events errors."""

    exit_code = 1


class ConfigError(IcalEventsError):
    """Configuration file is missing, unreadable, or invalid."""

    exit_code = 1


class CalendarError(IcalEventsError):
    """Calendar data could not be fetched or parsed."""

    exit_code = 2


class TemplateRenderError(IcalEventsError):
    """HTML template rendering failed."""

    exit_code = 3


class OutputWriteError(IcalEventsError):
    """Output file could not be written."""

    exit_code = 4


class DeployError(IcalEventsError):
    """Post-generation deploy step failed."""

    exit_code = 5
