from __future__ import annotations

from shared.configuration.profile_runtime import RuntimeProfileResolver


def test_runtime_profile_resolver_applies_inheritance() -> None:
    profiles = {
        "base": {"app": {"name": "pesaguard", "debug": False}},
        "development": {"extends": "base", "app": {"debug": True}},
    }

    resolved = RuntimeProfileResolver(profiles).resolve("development")

    assert resolved["app"]["name"] == "pesaguard"
    assert resolved["app"]["debug"] is True
