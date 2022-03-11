import datetime
import uuid
from typing import Any

import funcy
import orjson
import pendulum
from loguru import logger
from pypika import Query, Schema, Table

from devseed import config, db

_TRANSFORMATIONS = {
    "uuid4()": lambda: str(uuid.uuid4()),
    "current_time()": lambda: utc_now(),
}

# make sure we didn't forget to add () suffix to indicate callable
assert all(key.endswith("()") for key in _TRANSFORMATIONS)


def dict_to_sql(schema: str, table_name: str, elem: dict) -> str:
    transformed = funcy.walk_values(postgres_format, elem)

    return _to_query(schema, table_name, transformed)


def utc_now():
    return pendulum.now().in_tz("UTC")


def _to_query(schema: str, tbl: str, dct: dict[str, Any]):
    cols, vals = zip(*dct.items())

    table = Table(tbl, schema=Schema(schema) if schema else None)
    return Query.into(table).columns(cols).insert(vals)


def _fmt_time(dtime):
    dtime.in_tz("UTC").strftime(config.DB_TIME_FORMAT)


def to_yaml(value, *, compact: bool = False) -> str:
    try:
        if isinstance(value, str):
            return f'"{value}"' if any(char in value for char in (":", "[")) else value

        if isinstance(value, (pendulum.DateTime, datetime.datetime)):
            new_val = pendulum.instance(value).in_tz("UTC")
            return f'"{new_val}"'

        if isinstance(value, dict):
            if compact:
                new_val = {key: val for key, val in value.items() if val}
            else:
                new_val = value
            return jsonize(jsonize(new_val))

        if value is None:
            return "null"

        return value
    except TypeError:
        logger.error(f"unable to serialize {type(value)} {value} to YAML")
        raise


def postgres_format(val):
    try:
        if isinstance(val, datetime.datetime):
            return _fmt_time(pendulum.instance(val))

        if isinstance(val, list):
            # note: this could be made recursive, but usually data in arrays is not handled
            # by postgres, so for now we just store it as array string
            return db.pg_array(val)

        if isinstance(val, dict):
            # note: this could be made recursive, but usually data in arrays is not handled
            # by postgres, so for now we just store it as array string
            return orjson.dumps(val)

        if trn_value := _TRANSFORMATIONS.get(val):
            return trn_value() if callable(trn_value) else trn_value

        return val
    except TypeError:
        logger.error(f"unable to convert {val} for Postgres")
        raise


def jsonize(value: Any) -> str:
    return orjson.dumps(value).decode()
