from pathlib import Path

import environs

env = environs.Env()

_XDG_CONFIG_HOME = env.path("XDG_CONFIG_HOME")
_HOME = env.path("HOME")

_CONFIG_BASE = (
    (_XDG_CONFIG_HOME / "devseed")
    if _XDG_CONFIG_HOME.exists()
    else (_HOME / ".devseed")
)
CFG_PATH = _CONFIG_BASE / "devseedrc"
DB_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

DEFAULT_SEED_DIR = Path("db/seed")
DEFAULT_GLOB = "*.yml"
