import datetime
import logging
import uuid
from typing import Any

import funcy
import pendulum
from pypika import Query, Table

from devseed import config

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


def _to_query(tbl: str, dct: dict[str, Any]):
    cols, vals = zip(*dct.items())
    return Query.into(Table(tbl)).columns(cols).insert(vals)


def transform(val):
    if trn_value := _TRANSFORMATIONS.get(val):
        return trn_value() if callable(trn_value) else trn_value

    if isinstance(val, datetime.datetime):
        return _fmt_time(pendulum.instance(val))

    return val


def _fmt_time(dtime):
    dtime.in_tz("UTC").strftime(config.DB_TIME_FORMAT)


def _seed_to_db(table_name: str, elem: dict) -> str:
    transformed = funcy.walk_values(transform, elem)

    return _to_query(table_name, transformed)
