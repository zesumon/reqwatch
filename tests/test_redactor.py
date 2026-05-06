"""Tests for reqwatch.redactor."""

import pytest

from reqwatch.redactor import (
    DEFAULT_REDACT_PLACEHOLDER,
    RedactError,
    redact_keys_from_config,
    redact_snapshot,
)


@pytest.fixture()
def base_snapshot():
    return {
        "url": "https://example.com/api",
        "status": 200,
        "body": {
            "user": "alice",
            "token": "secret-abc",
            "profile": {
                "email": "alice@example.com",
                "api_key": "key-xyz",
            },
        },
    }


def test_redact_top_level_key(base_snapshot):
    result = redact_snapshot(base_snapshot, ["token"])
    assert result["body"]["token"] == DEFAULT_REDACT_PLACEHOLDER
    assert result["body"]["user"] == "alice"


def test_redact_nested_key(base_snapshot):
    result = redact_snapshot(base_snapshot, ["api_key"])
    assert result["body"]["profile"]["api_key"] == DEFAULT_REDACT_PLACEHOLDER
    assert result["body"]["profile"]["email"] == "alice@example.com"


def test_redact_multiple_keys(base_snapshot):
    result = redact_snapshot(base_snapshot, ["token", "email"])
    assert result["body"]["token"] == DEFAULT_REDACT_PLACEHOLDER
    assert result["body"]["profile"]["email"] == DEFAULT_REDACT_PLACEHOLDER


def test_redact_missing_key_is_noop(base_snapshot):
    result = redact_snapshot(base_snapshot, ["nonexistent"])
    assert result["body"] == base_snapshot["body"]


def test_redact_does_not_mutate_original(base_snapshot):
    original_token = base_snapshot["body"]["token"]
    redact_snapshot(base_snapshot, ["token"])
    assert base_snapshot["body"]["token"] == original_token


def test_redact_custom_placeholder(base_snapshot):
    result = redact_snapshot(base_snapshot, ["token"], placeholder="[HIDDEN]")
    assert result["body"]["token"] == "[HIDDEN]"


def test_redact_list_body():
    snapshot = {"url": "x", "status": 200, "body": [{"password": "s3cr3t"}, {"ok": True}]}
    result = redact_snapshot(snapshot, ["password"])
    assert result["body"][0]["password"] == DEFAULT_REDACT_PLACEHOLDER
    assert result["body"][1]["ok"] is True


def test_redact_no_body_key():
    snapshot = {"url": "x", "status": 200}
    result = redact_snapshot(snapshot, ["token"])
    assert "body" not in result


def test_redact_invalid_snapshot_raises():
    with pytest.raises(RedactError):
        redact_snapshot("not a dict", ["key"])  # type: ignore[arg-type]


def test_redact_invalid_keys_raises(base_snapshot):
    with pytest.raises(RedactError):
        redact_snapshot(base_snapshot, "token")  # type: ignore[arg-type]


def test_redact_keys_from_config_present():
    cfg = {"url": "x", "redact": ["token", "api_key"]}
    assert redact_keys_from_config(cfg) == ["token", "api_key"]


def test_redact_keys_from_config_absent():
    assert redact_keys_from_config({"url": "x"}) == []


def test_redact_keys_from_config_invalid_raises():
    with pytest.raises(RedactError):
        redact_keys_from_config({"redact": "token"})
