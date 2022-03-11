import pytest

from devseed.transformers import to_yaml


@pytest.fixture
def a_dict():
    return {"age": 42, "email": "", "name": None}


def test_to_yaml(a_dict):
    assert to_yaml(a_dict) == '"{\\"age\\":42,\\"email\\":\\"\\",\\"name\\":null}"'


def test_to_yaml_with_compact(a_dict):
    assert to_yaml(a_dict, compact=True) == '"{\\"age\\":42}"'
