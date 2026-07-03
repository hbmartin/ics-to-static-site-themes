"""Data models for configuration and template events."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator


class SiteConfig(BaseModel):
    title: str
    description: str
    homepage_url: str | None = None
    x_username: str | None = None


class CategoryFilters(BaseModel):
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)

    def allows(self, categories: list[str]) -> bool:
        """Return True if an event with these categories passes the filter."""
        lowered = {c.lower() for c in categories}
        if self.include and not lowered & {c.lower() for c in self.include}:
            return False
        return not (self.exclude and lowered & {c.lower() for c in self.exclude})


class FiltersConfig(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    max_events: int | None = None
    categories: CategoryFilters = Field(default_factory=CategoryFilters)

    def effective_start_date(self, today: date) -> date:
        return self.start_date if self.start_date is not None else today

    def effective_end_date(self, today: date) -> date:
        if self.end_date is not None:
            return self.end_date
        return today.replace(year=today.year + 1)


class MetaConfig(BaseModel):
    image: str | None = None
    custom: dict[str, str] = Field(default_factory=dict)


class StructuredDataOrg(BaseModel):
    name: str
    url: str
    logo: str | None = None


class StructuredDataConfig(BaseModel):
    organization: StructuredDataOrg | None = None


class OutputConfig(BaseModel):
    file: str = "./events/index.html"


class CalendarSource(BaseModel):
    source: str
    label: str | None = None
    color: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_str(cls, value: object) -> object:
        if isinstance(value, str):
            return {"source": value}
        return value


class Config(BaseModel):
    model_config = {"populate_by_name": True}

    calendar: CalendarSource | list[CalendarSource]
    site: SiteConfig
    timezone: str | None = None
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    meta: MetaConfig = Field(default_factory=MetaConfig)
    structured_data: StructuredDataConfig = Field(default_factory=StructuredDataConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    wrangler_pages_project: str | None = Field(
        default=None, alias="wrangler-pages-project"
    )

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str | None) -> str | None:
        if value is not None:
            try:
                ZoneInfo(value)
            except (KeyError, ValueError) as e:
                raise ValueError(f"Unknown timezone: {value}") from e
        return value

    @property
    def calendar_sources(self) -> list[CalendarSource]:
        if isinstance(self.calendar, list):
            return self.calendar
        return [self.calendar]

    def tzinfo(self) -> ZoneInfo | None:
        return ZoneInfo(self.timezone) if self.timezone else None


class TemplateEvent(BaseModel):
    uid: str
    instance_id: str = ""
    summary: str
    description: str | None = None
    location: str | None = None
    url: str | None = None
    start_date: date
    end_date: date | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    is_all_day: bool = True
    categories: list[str] = Field(default_factory=list)
    month_key: str = ""
    anchor_id: str = ""
    date_display: str = ""
    time_display: str | None = None
    duration_days: int = 1
    source_label: str | None = None
    source_color: str | None = None

    @model_validator(mode="after")
    def _default_instance_id(self) -> TemplateEvent:
        if not self.instance_id:
            self.instance_id = self.uid
        return self
