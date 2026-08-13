from __future__ import annotations


class ConfigurationError(Exception):
    """Base exception raised for configuration loading and validation failures."""


class ConfigurationNotFoundError(ConfigurationError):
    """Raised when configuration cannot be located."""