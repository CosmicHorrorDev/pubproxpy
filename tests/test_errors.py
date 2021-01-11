import json

import pytest
from httmock import HTTMock, urlmatch  # type: ignore

from pubproxpy import ProxyFetcher, errors
from tests.constants import ASSETS_DIR


@urlmatch(netloc=r"pubproxy\.com")
def bad_key_resp(_url, _request):
    with (ASSETS_DIR / "bad_key_resp.json").open() as f:
        return json.load(f)


def test_bad_key_resp() -> None:
    with HTTMock(bad_key_resp):
        with pytest.raises(errors.APIKeyError):
            ProxyFetcher(api_key="<invalid>").get()


@urlmatch(netloc=r"pubproxy\.com")
def rate_limit_resp(_url, _request) -> dict:
    with (ASSETS_DIR / "rate_limit_resp.json").open() as f:
        return json.load(f)


def test_rate_limit() -> None:
    with HTTMock(rate_limit_resp):
        with pytest.raises(errors.RateLimitError):
            ProxyFetcher().get()


@urlmatch(netloc=r"pubproxy\.com")
def daily_limit_resp(_url, _request) -> dict:
    with (ASSETS_DIR / "daily_limit_resp.json").open() as f:
        return json.load(f)


def test_daily_limit_resp() -> None:
    with HTTMock(daily_limit_resp):
        with pytest.raises(errors.DailyLimitError):
            ProxyFetcher().get()


@urlmatch(netloc=r"pubproxy\.com")
def no_proxy_resp(_url, _request) -> dict:
    with (ASSETS_DIR / "no_proxy_resp.json").open() as f:
        return json.load(f)


def test_no_proxy_resp() -> None:
    with HTTMock(no_proxy_resp):
        with pytest.raises(errors.NoProxyError):
            ProxyFetcher(countries=["AH"]).get()
