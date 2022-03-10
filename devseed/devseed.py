import sys
from pathlib import Path
from typing import Any, TextIO

import rich
import typer
import yaml
from pg8000.exceptions import DatabaseError

from devseed import __version__, config, db, transformers
from devseed.errors import InvalidEntry
from devseed.types import Params

app = typer.Typer()


# Main entry point for app
@app.command()
def seed(
    seed_dir: Path = config.DEFAULT_SEED_DIR,
    verbose: bool = False,
    db_name: str = "postgres",
    dry_run: bool = False,
    force: bool = False,
    schema: str = "",
    glob: str = config.DEFAULT_GLOB,
    limit: int = 10000,
    import_from: str | None = None,
    out: Path | None = None,
    version: bool = False,
):
    if version:
        typer.echo(__version__)
        sys.exit(0)

    if verbose:
        typer.echo(f"Using {config.CFG_PATH} as config file")

    ctx = Params(
        seed_dir=seed_dir,
        verbose=verbose,
        db_name=db_name,
        dry_run=dry_run,
        force=force,
        schema=schema,
        glob=glob,
        limit=limit,
        import_from=import_from,
        out=out,
    )
    try:
        with db.build_conn(db_name=db_name, dry_run=dry_run) as conn:
            # TODO: replace with dispatcher
            if import_from:
                if not out:
                    abort("--out needed for importing data")

                assert out
                if out.exists() and not force:
                    abort(f"Output file {out} already exists, quitting")

                with out.open("w") as fh:
                    import_yaml_from_table(ctx, conn, fh)
            else:
                insert(conn, schema, seed_dir, glob)
    except DatabaseError as exc:
        # TODO: cleanup
        err = exc.args[0]
        msg = err["M"]
        detail = err["D"]
        abort(f"{msg}\n{detail}")


def import_yaml_from_table(ctx: Params, conn, out: TextIO):
    cols, records = db.table_sample(ctx, conn)

    # TODO: ugly & move to transformers
    out.write("---\n")  # not needed, but good practise in YAML
    for rec in records:
        for idx, (key, val) in enumerate(zip(cols, rec)):
            indent = "- " if idx == 0 else "  "
            val = transformers.to_yaml_value(ctx, val)
            out.write(f"{indent}{key}: {val}\n")


def abort(msg):
    rich.print(f"[red]{msg}[/red]")
    sys.exit(1)


def insert(db_conn, schema: str, seed_dir: Path, glob: str) -> None:
    cur = db_conn.cursor()

    for query in files_to_sql(seed_dir, glob, schema=schema):
        cur.execute(str(query))
    db_conn.commit()


def files_to_sql(seed_dir: Path, glob: str, schema: str = ""):
    for pth in seed_dir.rglob(glob):
        entries = _parse_yaml(pth)

        if isinstance(entries, dict):
            if len(entries) != 1:
                raise InvalidEntry(
                    "expected exactly one table name (or not giving list of entries)"
                )
            yield from _entry_dict_gen(entries, schema)

        elif isinstance(entries, list):
            yield from _entry_list_gen(entries, pth, schema)


def _parse_yaml(fpath: Path) -> dict[str, Any]:
    with fpath.open() as fh:
        return yaml.safe_load(fh)


def _entry_list_gen(entries, pth, schema):
    for entry in entries:
        yield transformers.dict_to_sql(schema, pth.stem, entry)


def _entry_dict_gen(entries, schema):
    for tbl, val in entries.items():
        for entry in val:
            yield transformers.dict_to_sql(schema, tbl, entry)
