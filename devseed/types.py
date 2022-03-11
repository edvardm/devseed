from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImportParams:
    db_name: str
    dry_run: bool
    force: bool
    import_from: str
    limit: int
    schema: str
    verbose: bool

    compact: bool = False
    out: Path = Path("-")
