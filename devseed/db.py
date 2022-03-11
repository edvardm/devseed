import sys
from typing import Any

import pg8000.dbapi as pg

from devseed import errors, types


def output(msg):
    sys.stderr.write(f"{msg}\n")


class NullCursor:
    def execute(self, *args):
        output(" ".join(args))


class NullConn:
    # Class to mock db connection. It only prints out commands
    def __init__(self, db: str):
        self.db = db

    def connect(self, **kwargs) -> None:
        ...

    def cursor(self) -> NullCursor:
        return NullCursor()

    def commit(self):
        ...

    # Allow use as context manager
    def __enter__(self):
        return self

    def __exit__(self, _exception_type, exception_value, _exception_traceback):
        if err := exception_value:
            raise errors.DatabaseError(_rewrap_exc(err))


def _rewrap_exc(exc):
    msg = [exc["M"]]
    if detail := exc.get("D"):
        msg.append(detail)

    return "\n".join(msg)


def build_conn(
    *,
    db_name: str = "postgres",
    db_user: str = "postgres",
    dry_run: bool = False,
    verbose=False,
):
    if verbose and not dry_run:
        print(f"connecting to {db_name=} as {db_user}")

    return NullConn(db_name) if dry_run else pg.connect(database=db_name, user=db_user)


def table_sample(ctx: types.ImportParams, conn):
    # Read entries from table. As seed data should contain rather
    # small amount of records for people to easily understand/know
    # what is there, hence limit

    cur = conn.cursor()

    # TODO: use Pypika to build this, improves security too
    tbl = quote_table(ctx.schema, ctx.import_from)
    query = f"SELECT * from {tbl} ORDER BY random() LIMIT {ctx.limit}"  # nosec
    if ctx.verbose:
        output(query)

    cur.execute(query)

    # get column names
    cols = [tpl[0] for tpl in cur.description]

    # cur.fetchmany() would be cleaner if we had large amounts of data,
    # but for this fetchall() should be fine
    return cols, cur.fetchall()


def quote_table(schema, tbl_name) -> str:
    return f'"{schema}".{tbl_name}' if schema else tbl_name


def pg_array(values: list[Any]) -> str:
    return "{{{}}}".format(", ".join(values))
