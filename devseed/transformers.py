import datetime
import logging
import uuid
from typing import Any

import funcy
import pendulum
from pypika import Query, Schema, Table

from devseed import config
from devseed.types import Params

_TRANSFORMATIONS = {
    "uuid4()": lambda: str(uuid.uuid4()),
    "current_time()": lambda: utc_now(),
}


def utc_now():
    return pendulum.now().in_tz("UTC")


# make sure we didn't forget to add () suffix to indicate callable
assert all(key.endswith("()") for key in _TRANSFORMATIONS.keys())


def warn(msg):
    logging.warning(msg)


def _to_query(schema: str, tbl: str, dct: dict[str, Any]):
    cols, vals = zip(*dct.items())

    table = Table(tbl, schema=Schema(schema) if schema else None)
    return Query.into(table).columns(cols).insert(vals)


def transform(val):
    if trn_value := _TRANSFORMATIONS.get(val):
        return trn_value() if callable(trn_value) else trn_value

    if isinstance(val, datetime.datetime):
        return _fmt_time(pendulum.instance(val))

    return val


def _fmt_time(dtime):
    dtime.in_tz("UTC").strftime(config.DB_TIME_FORMAT)


def dict_to_sql(schema: str, table_name: str, elem: dict) -> str:
    transformed = funcy.walk_values(transform, elem)

    return _to_query(schema, table_name, transformed)


def to_yaml_value(ctx: Params, val):
    del ctx  # Unused
    # print(val, type(val))
    if val is None:
        return "null"

    if isinstance(val, str):
        return f'"{val}"' if any(char in val for char in (":", "[")) else val

    if isinstance(val, (pendulum.DateTime, datetime.datetime)):
        new_val = pendulum.instance(val).in_tz("UTC")
        return f'"{new_val}"'

    return val
