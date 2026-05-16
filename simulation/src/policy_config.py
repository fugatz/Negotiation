from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .common import ROOT


POLICY_CONFIG_PATH = ROOT / "config" / "policy.json"


@lru_cache
def load_policy_config(path: Path = POLICY_CONFIG_PATH) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def policy_version() -> str:
    return str(load_policy_config()["version"])
