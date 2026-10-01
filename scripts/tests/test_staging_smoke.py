from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from scripts.staging_smoke import check_health


def test_health_check_requests_only_public_health_paths():
    responses = [MagicMock(status=200), MagicMock(status=200)]
    for response in responses:
        response.__enter__.return_value = response

    with patch("scripts.staging_smoke.urlopen", side_effect=responses) as open_url:
        assert check_health("https://api-staging.birky.com") == [
            ("/api/health/live/", 200),
            ("/api/health/ready/", 200),
        ]

    assert open_url.call_count == 2
    assert all(call.args[0].get_method() == "GET" for call in open_url.call_args_list)


@pytest.mark.parametrize(
    "base_url",
    [
        "file:///etc/passwd",
        "https://user:password@example.test",
        "https://example.test/path?token=secret",
        "https://example.test/#secret",
    ],
)
def test_health_check_rejects_non_origin_or_credentialed_urls(base_url):
    with pytest.raises(ValueError):
        check_health(base_url)


def test_health_check_returns_non_200_status_without_response_body():
    forbidden = HTTPError(
        "https://api-staging.birky.com/api/health/ready/",
        503,
        "unavailable",
        hdrs=None,
        fp=None,
    )
    success = MagicMock(status=200)
    success.__enter__.return_value = success
    with patch("scripts.staging_smoke.urlopen", side_effect=[success, forbidden]):
        assert check_health("https://api-staging.birky.com") == [
            ("/api/health/live/", 200),
            ("/api/health/ready/", 503),
        ]
