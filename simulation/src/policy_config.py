from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .common import ROOT


POLICY_CONFIG_PATH = ROOT / "config" / "policy.json"
_active_policy_config_path = POLICY_CONFIG_PATH.resolve()


def _resolve_path(path: str | Path) -> Path:
    config_path = Path(path).expanduser()
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    return config_path.resolve()


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@lru_cache
def _load_policy_config(path: str) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open() as handle:
        raw = json.load(handle)

    extends = raw.pop("extends", None)
    if not extends:
        return raw

    base_path = (config_path.parent / str(extends)).resolve()
    return _deep_merge(_load_policy_config(str(base_path)), raw)


def configure_policy_config(path: str | Path) -> None:
    global _active_policy_config_path
    _active_policy_config_path = _resolve_path(path)


def active_policy_config_path() -> Path:
    return _active_policy_config_path


def active_policy_config_relative_path() -> str:
    try:
        return str(_active_policy_config_path.relative_to(ROOT.parent))
    except ValueError:
        return str(_active_policy_config_path)


def load_policy_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = _active_policy_config_path if path is None else _resolve_path(path)
    return _load_policy_config(str(config_path))


def policy_version() -> str:
    return str(load_policy_config()["version"])
