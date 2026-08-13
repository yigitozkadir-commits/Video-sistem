"""
Minimal feature flags. Deliberately not a service or a database - a flag
is just a boolean this repo's scripts check before doing something
optional/risky. Two sources, checked in this order:

1. Environment variable: FLAG_<NAME>=1 or 0/true/false
2. studio.config.json's "feature_flags" object (added on first use, empty
   by default so existing behavior is unchanged until a flag is set)

Env wins over the config file, so a one-off override never requires
editing a committed file.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent.parent / "studio.config.json"

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def is_enabled(name: str, default: bool = False) -> bool:
    env_val = os.getenv(f"FLAG_{name.upper()}")
    if env_val is not None:
        if env_val.lower() in _TRUE:
            return True
        if env_val.lower() in _FALSE:
            return False

    if _CONFIG_PATH.exists():
        cfg = json.loads(_CONFIG_PATH.read_text())
        flags = cfg.get("feature_flags", {})
        if name in flags:
            return bool(flags[name])

    return default
