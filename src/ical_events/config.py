"""Configuration loading and validation."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from .models import Config


def load_config(config_path: str) -> Config:
    """Load and validate a YAML configuration file.

    Returns validated Config or exits with code 1 on error.
    """
    path = Path(config_path)

    if not path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error: Cannot read config file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in config file: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("Error: Config file must contain a YAML mapping", file=sys.stderr)
        sys.exit(1)

    try:
        return Config.model_validate(data)
    except ValidationError as e:
        print(f"Error: Invalid configuration:\n{e}", file=sys.stderr)
        sys.exit(1)
