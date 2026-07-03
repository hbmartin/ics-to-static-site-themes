"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from .exceptions import ConfigError
from .models import Config


def load_config(config_path: str) -> Config:
    """Load and validate a YAML configuration file.

    Raises ConfigError on any problem.
    """
    path = Path(config_path)

    if not path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"Cannot read config file: {e}") from e

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a YAML mapping")

    try:
        return Config.model_validate(data)
    except ValidationError as e:
        raise ConfigError(f"Invalid configuration:\n{e}") from e
