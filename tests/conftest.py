"""Shared test fixtures."""

from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_ics_path():
    return FIXTURES_DIR / "sample.ics"


@pytest.fixture
def sample_ics_content(sample_ics_path):
    return sample_ics_path.read_text(encoding="utf-8")


@pytest.fixture
def sample_config_path():
    return FIXTURES_DIR / "sample_config.yaml"
