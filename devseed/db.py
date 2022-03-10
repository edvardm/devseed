import sys

import pg8000.dbapi as pg

from devseed.types import Params


def output(msg):
    sys.stdout.write(f"{msg}\n")


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

    def __exit__(self, *args):
        ...


def build_conn(
    *, db_name: str = "postgres", db_user: str = "postgres", dry_run: bool = False
):
    print(f"connecting to {db_name=} as {db_user}")
    return NullConn(db_name) if dry_run else pg.connect(database=db_name, user=db_user)


def table_sample(
    ctx: Params,
    conn,
):
    # Read entries from table. As seed data should contain rather
    # small amount of records for people to easily understand/know
    # what is there, hence limit

    def quote(tbl_name):
        return f'"{ctx.schema}".{tbl_name}' if ctx.schema else tbl_name

    cur = conn.cursor()
    table = ctx.import_from

    query = f"SELECT * from {quote(table)} ORDER BY random() LIMIT {ctx.limit}"
    if ctx.verbose:
        output(query)

    cur.execute(query)

    # get column names
    cols = [tpl[0] for tpl in cur.description]

    # cur.fetchmany() would be cleaner if we had large amounts of data,
    # but for this fetchall() should be fine
    return cols, cur.fetchall()
