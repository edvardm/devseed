from pathlib import Path

import pendulum
from pypika import Query

from devseed import devseed

FIXTURES = Path("tests/fixtures")


def describe_successful_parsing_of_fixtures():
    def infers_table_from_filename():
        parsed = parse_me("people.yml")

        assert str(parsed) == str(
            Query.into("people")
            .columns("id", "firstname", "lastname", "age")
            .insert(1, "Bob", "Bobbydale", 42)
        )

    def reads_table_name_from_top_key_when_present():
        parsed = parse_me("table_name_in_file.yml")

        assert str(parsed) == str(
            Query.into("people")
            .columns("id", "firstname", "lastname", "age")
            .insert(99, "Alice", "Alison", 42)
        )

    def transforms_values(module_mocker):
        module_mocker.patch("uuid.uuid4", lambda: "deadbeef-cafe")
        module_mocker.patch(
            "devseed.transformers.utc_now",
            lambda: pendulum.parse("2022-03-05T14:00:00+00:00"),
        )

        parsed = parse_me("transformations.yml")

        assert str(parsed) == str(
            Query.into("transformations")
            .columns("long_id", "typing", "created_at")
            .insert("deadbeef-cafe", "static", "2022-03-05T14:00:00+00:00")
        )


def parse_me(fpath):
    return next(devseed.files_to_sql(FIXTURES, fpath))
