import json

import pytest
from httmock import HTTMock, urlmatch  # type: ignore

from pubproxpy import ProxyFetcher, errors
from tests.constants import ASSETS_DIR


@urlmatch(netloc=r"pubproxy\.com")
def bad_key_resp(_url, _request):
    with (ASSETS_DIR / "bad_key_resp.json").open() as f:
        return json.load(f)


@urlmatch(netloc=r"pubproxy\.com")
def rate_limit_resp(_url, _request) -> dict:
    with (ASSETS_DIR / "rate_limit_resp.json").open() as f:
        return json.load(f)


@urlmatch(netloc=r"pubproxy\.com")
def daily_limit_resp(_url, _request) -> dict:
    with (ASSETS_DIR / "daily_limit_resp.json").open() as f:
        return json.load(f)


@urlmatch(netloc=r"pubproxy\.com")
def no_proxy_resp(_url, _request) -> dict:
    with (ASSETS_DIR / "no_proxy_resp.json").open() as f:
        return json.load(f)


def test_bad_key_resp() -> None:
    RESP_ERR_MAP = [
        (bad_key_resp, errors.APIKeyError),
        (rate_limit_resp, errors.RateLimitError),
        (daily_limit_resp, errors.DailyLimitError),
        (no_proxy_resp, errors.NoProxyError),
    ]

    for resp, err in RESP_ERR_MAP:
        with HTTMock(resp):
            with pytest.raises(err):
                ProxyFetcher().get()
