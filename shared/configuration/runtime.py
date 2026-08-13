from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from shared.configuration.exceptions.config_exception import ConfigurationError
from shared.configuration.interfaces import ConfigurationReloadHook
from shared.configuration.loader import ConfigurationLoader
from shared.configuration.manager import ConfigurationManager

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # pragma: no cover
    FileSystemEventHandler = object
    Observer = None


class ConfigFileChangeHandler(FileSystemEventHandler):
    def __init__(self, reload_callback: callable[[], None]) -> None:
        self.reload_callback = reload_callback

    def on_modified(self, event: Any) -> None:
        if getattr(event, "is_directory", False):
            return
        self.reload_callback()


class RuntimeConfigurationManager(ConfigurationManager):
    """Runtime manager with watch support, snapshots, and startup validation."""

    def __init__(self, config_path: str | None = None, *, reload_hooks: list[ConfigurationReloadHook] | None = None) -> None:
        super().__init__(config_path, reload_hooks=reload_hooks)
        self.watcher: Observer | None = None
        self.handled_path = str(Path(self.config_path or os.environ.get("PESAGUARD_CONFIG_PATH") or "/etc/pesaguard/pesaguard.config.json"))

    def _watch_supported(self) -> bool:
        return Observer is not None

    def validate_startup(self) -> None:
        config = self.get_config()
        if config.environment.value not in {"development", "testing", "staging", "production"}:
            raise ConfigurationError(f"Unsupported environment '{config.environment}'")
        if not config.app_name:
            raise ConfigurationError("Application name must be set")
        if not config.security.jwt_secret.get_secret_value():
            raise ConfigurationError("JWT secret must be provided")
        if not config.security.encryption_key.get_secret_value():
            raise ConfigurationError("Encryption key must be provided")

    def start_watch(self) -> None:
        if not self._watch_supported():
            raise ConfigurationError("watchdog is required to start configuration file watching")
        if self.watcher is not None:
            return
        handler = ConfigFileChangeHandler(self.reload)
        self.watcher = Observer()
        self.watcher.schedule(handler, str(Path(self.handled_path).parent), recursive=False)
        self.watcher.start()

    def stop_watch(self) -> None:
        if self.watcher is None:
            return
        self.watcher.stop()
        self.watcher.join()
        self.watcher = None

    def snapshot_to_file(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        snapshot = self.snapshot()
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=2)
