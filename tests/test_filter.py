import pytest
from reqwatch.filter import apply_exclude, apply_include, filter_body, FilterError


@pytest.fixture
def sample_body():
    return {
        "id": 1,
        "name": "Alice",
        "meta": {
            "created_at": "2024-01-01",
            "updated_at": "2024-06-01",
            "version": 3,
        },
        "tags": ["a", "b"],
    }


def test_exclude_top_level_key(sample_body):
    result = apply_exclude(sample_body, ["id"])
    assert "id" not in result
    assert "name" in result


def test_exclude_nested_key(sample_body):
    result = apply_exclude(sample_body, ["meta.updated_at"])
    assert "updated_at" not in result["meta"]
    assert "created_at" in result["meta"]


def test_exclude_missing_key_is_noop(sample_body):
    result = apply_exclude(sample_body, ["nonexistent"])
    assert result == sample_body


def test_exclude_multiple_keys(sample_body):
    result = apply_exclude(sample_body, ["id", "meta.created_at", "meta.updated_at"])
    assert "id" not in result
    assert "created_at" not in result["meta"]
    assert "updated_at" not in result["meta"]
    assert result["meta"]["version"] == 3


def test_include_top_level_keys(sample_body):
    result = apply_include(sample_body, ["id", "name"])
    assert result == {"id": 1, "name": "Alice"}


def test_include_nested_key(sample_body):
    result = apply_include(sample_body, ["meta.version"])
    assert result == {"meta": {"version": 3}}


def test_include_missing_key_omitted(sample_body):
    result = apply_include(sample_body, ["id", "ghost"])
    assert result == {"id": 1}


def test_include_raises_on_non_dict():
    with pytest.raises(FilterError):
        apply_include(["not", "a", "dict"], ["key"])


def test_filter_body_include_and_exclude(sample_body):
    result = filter_body(
        sample_body,
        include_keys=["meta"],
        exclude_keys=["meta.updated_at"],
    )
    assert "created_at" in result["meta"]
    assert "updated_at" not in result["meta"]
    assert "id" not in result


def test_filter_body_no_filters_returns_original(sample_body):
    result = filter_body(sample_body)
    assert result == sample_body


def test_filter_body_non_dict_with_exclude():
    result = filter_body("plain string", exclude_keys=["key"])
    assert result == "plain string"
