"""Unit tests for reqwatch.fetcher using responses mock library."""

import pytest
import responses as rsps_lib
from responses import RequestsMock

from reqwatch.fetcher import fetch_response


@rsps_lib.activate
def test_successful_json_fetch():
    rsps_lib.add(rsps_lib.GET, "https://api.example.com/data",
                 json={"key": "value"}, status=200)

    result = fetch_response("https://api.example.com/data")

    assert result["status_code"] == 200
    assert result["body"] == {"key": "value"}
    assert result["error"] is None
    assert result["method"] == "GET"
    assert "fetched_at" in result
    assert result["elapsed_seconds"] >= 0


@rsps_lib.activate
def test_non_json_body_falls_back_to_text():
    rsps_lib.add(rsps_lib.GET, "https://api.example.com/plain",
                 body="hello world", status=200,
                 content_type="text/plain")

    result = fetch_response("https://api.example.com/plain")
    assert result["body"] == "hello world"


@rsps_lib.activate
def test_http_error_status_is_captured():
    rsps_lib.add(rsps_lib.GET, "https://api.example.com/gone",
                 json={"detail": "not found"}, status=404)

    result = fetch_response("https://api.example.com/gone")
    assert result["status_code"] == 404
    assert result["error"] is None


@rsps_lib.activate
def test_connection_error_sets_error_field():
    rsps_lib.add(rsps_lib.GET, "https://unreachable.example.com/",
                 body=Exception("connection refused"))

    result = fetch_response("https://unreachable.example.com/")
    assert result["status_code"] is None
    assert result["error"] is not None
    assert "connection refused" in result["error"]


@rsps_lib.activate
def test_post_method_sends_body():
    def request_callback(request):
        import json
        payload = json.loads(request.body)
        return (201, {}, json.dumps({"received": payload}))

    rsps_lib.add_callback(rsps_lib.POST, "https://api.example.com/items",
                          callback=request_callback,
                          content_type="application/json")

    result = fetch_response("https://api.example.com/items",
                            method="POST", body={"name": "test"})
    assert result["status_code"] == 201
    assert result["body"]["received"]["name"] == "test"
