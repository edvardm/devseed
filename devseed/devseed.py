from pathlib import Path
from typing import Any

import pg8000.dbapi as pg
import typer
import yaml

from devseed import config
from devseed.errors import InvalidEntry
from devseed.transformers import _seed_to_db

DEFAULT_SEED_DIR = Path("db/seed")

app = typer.Typer()


def _parse_yaml(fpath: Path) -> dict[str, Any]:
    with fpath.open() as fh:
        return yaml.safe_load(fh)


class NullCursor:
    def execute(self, *args):
        typer.echo(" ".join(args))


class NullConn:
    def __init__(self, db: str):
        self.db = db

    def connect(self, **kwargs) -> None:
        typer.echo(kwargs)

    def cursor(self) -> NullCursor:
        return NullCursor()

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        del args  # Unused


def _build_conn(
    *, db_name: str = "postgres", db_user: str = "postgres", dry_run: bool = False
):
    return NullConn(db_name) if dry_run else pg.connect(database=db_name, user=db_user)


# Main entry point for app
@app.command()
def seed(
    seed_dir: Path = DEFAULT_SEED_DIR,
    verbose: bool = False,
    db: str = "postgres",
    dry_run: bool = False,
):
    if verbose:
        typer.echo(f"Using {config.CFG_PATH} as config file")

    with _build_conn(db_name=db, dry_run=dry_run) as db_conn:
        _insert(db_conn, seed_dir)


def _insert(db_conn, seed_dir: Path) -> None:
    cur = db_conn.cursor()

    for query in files_to_sql(seed_dir, "*.yml"):
        cur.execute(str(query))
    db_conn.commit()


def files_to_sql(seed_dir: Path = DEFAULT_SEED_DIR, glob: str = "*.yml"):
    for pth in seed_dir.rglob(glob):
        entries = _parse_yaml(pth)

        if isinstance(entries, dict):
            if len(entries) != 1:
                raise InvalidEntry(
                    "expected exactly one table name (or not giving list of entries)"
                )
            yield from _entry_dict_gen(entries)

        elif isinstance(entries, list):
            yield from _entry_list_gen(entries, pth)


def _entry_list_gen(entries, pth):
    for entry in entries:
        yield _seed_to_db(pth.stem, entry)


def _entry_dict_gen(entries):
    for tbl, val in entries.items():
        for entry in val:
            yield _seed_to_db(tbl, entry)
