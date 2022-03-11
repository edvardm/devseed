import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TextIO

import typer
import yaml
from pg8000 import exceptions as orig_exceptions

from devseed import __version__, config, control, db, errors, transformers, types

app = typer.Typer()


@app.command()
def version():
    typer.echo(__version__)


@app.command()
def seed(
    seed_dir: Path = typer.Option(config.DEFAULT_SEED_DIR, help="Seed data directory"),  # noqa: B008
    verbose: bool = typer.Option(False, help="Be more verbose"),  # noqa: B008
    db_name: str = typer.Option("postgres", help="Database to connect to"),  # noqa: B008
    dry_run: bool = typer.Option(False, help="Only show what would be done"),  # noqa: B008
    schema: str = typer.Option("", help="Schema to use for tables"),  # noqa: B008
    glob: str = typer.Option(config.DEFAULT_GLOB, help="file glob to match YAML files with"),  # noqa: B008
):
    if verbose:
        typer.echo(f"Using {config.CFG_PATH} as config file")

    try:
        with db.build_conn(db_name=db_name, dry_run=dry_run) as conn:
            if not seed_dir.exists() or not seed_dir.is_dir():
                control.abort(f"{seed_dir} does not exist or is not a directory")
            insert_all(conn, schema, seed_dir, glob, verbose)
    except orig_exceptions.DatabaseError as exc:
        control.abort(str(exc))


@app.command()
def db_import(
    table: str = typer.Argument(..., help="Table name to import from"),  # noqa: B008
    compact: bool = typer.Argument(  # noqa: B008
        types.ImportParams.compact, help="Remove blank values when possible"
    ),
    count: int = typer.Option(256, help="Sample size for import data"),  # noqa: B008
    db_name: str = typer.Option("postgres", help="Database to connect to"),  # noqa: B008
    dry_run: bool = typer.Option(False, help="Only show what would be done"),  # noqa: B008
    force: bool = typer.Option(False, help="Overwrite files instead of quitting"),  # noqa: B008
    out: Path = typer.Option("-", help="YAML output file path"),  # noqa: B008
    schema: str = typer.Option("", help="Schema to use for tables"),  # noqa: B008
    verbose: bool = typer.Option(False, help="Be more verbose"),  # noqa: B008
):
    @contextmanager
    def open_or_stdout(fpath: Path):
        if fpath.name == "-":
            yield sys.stdout
        else:
            with open(fpath, "w") as w_io:
                yield w_io

    if verbose:
        typer.echo(f"Using {config.CFG_PATH} as config file")

    ctx = types.ImportParams(
        compact=compact,
        db_name=db_name,
        dry_run=dry_run,
        force=force,
        import_from=table,
        limit=count,
        out=out,
        schema=schema,
        verbose=verbose,
    )
    try:
        with db.build_conn(db_name=db_name, dry_run=dry_run) as conn:
            if out.exists() and not force:
                control.abort(f"Output file {out} already exists, quitting")

            with open_or_stdout(out) as io:
                import_yaml_from_table(ctx, conn, io)
    except errors.DatabaseError as exc:
        control.abort(exc)


def import_yaml_from_table(ctx: types.ImportParams, conn, out: TextIO):
    cols, records = db.table_sample(ctx, conn)

    # TODO: ugly & move to transformers
    out.write("---\n")  # not needed, but good practise in YAML
    for rec in records:
        for idx, (key, val) in enumerate(zip(cols, rec)):
            indent = "- " if idx == 0 else "  "
            val = transformers.to_yaml(val)
            out.write(f"{indent}{key}: {val}\n")


def insert_all(db_conn, schema: str, seed_dir: Path, glob: str, verbose: bool) -> None:
    info = typer.echo if verbose else lambda _: _
    cur = db_conn.cursor()

    for pth in sorted(seed_dir.glob(glob)):
        info(f"Seeding entries in {pth}")

        count = 0
        for query in yaml_to_sql(pth, schema=schema):
            cur.execute(str(query))
            count += 1

        db_conn.commit()
        info(f"wrote {count} entries")


def yaml_to_sql(fpath: Path, schema: str = ""):
    entries = _parse_yaml(fpath)

    if isinstance(entries, dict):
        if len(entries) != 1:
            raise errors.InvalidEntry("expected exactly one table name (or not giving list of entries)")
        yield from _entry_dict_gen(entries, schema)

    elif isinstance(entries, list):
        yield from _entry_list_gen(entries, fpath, schema)


def _parse_yaml(fpath: Path) -> dict[str, Any]:
    with fpath.open() as fh:
        return yaml.safe_load(fh)


def _entry_list_gen(entries, pth: Path, schema: str):
    # Default case: YAML contains list of entries

    # strip any sort prefix if present
    tbl = re.sub(r"^\d+_", "", pth.stem)

    for entry in entries:
        yield transformers.dict_to_sql(schema, tbl, entry)


def _entry_dict_gen(entries, schema):
    # YAML file contained name of table to use
    for tbl, val in entries.items():
        for entry in val:
            yield transformers.dict_to_sql(schema, tbl, entry)


if __name__ == "__main__":
    app()
