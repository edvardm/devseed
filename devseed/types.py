from dataclasses import dataclass
from pathlib import Path


@dataclass
class Params:
    seed_dir: Path
    glob: str
    verbose: bool
    db_name: str
    dry_run: bool
    force: bool
    schema: str
    limit: int
    import_from: str | None
    out: Path | None
