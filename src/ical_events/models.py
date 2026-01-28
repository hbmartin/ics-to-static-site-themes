"""Data models for configuration and template events."""

from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, Field


class SiteConfig(BaseModel):
    title: str
    description: str
    homepage_url: str | None = None
    x_username: str | None = None


class FiltersConfig(BaseModel):
    start_date: date = Field(default_factory=date.today)
    end_date: date | None = None
    max_events: int | None = None

    def effective_end_date(self) -> date:
        if self.end_date is not None:
            return self.end_date
        today = date.today()
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


class Config(BaseModel):
    calendar: str
    site: SiteConfig
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    meta: MetaConfig = Field(default_factory=MetaConfig)
    structured_data: StructuredDataConfig = Field(default_factory=StructuredDataConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


class TemplateEvent(BaseModel):
    uid: str
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
    duration_days: int = 1
