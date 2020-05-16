import pytest
import requests

from datetime import datetime as dt
import json
import os
from unittest.mock import patch

from pubproxpy import ProxyFetcher


class _mock_resp:
    def __init__(self, text):
        self.text = text


PROXIES = [f"{i}.{i}.{i}.{i}:1234" for i in range(5)]
MOCK_RESP = _mock_resp(
    json.dumps({"data": [{"ipPort": proxy} for proxy in PROXIES]})
)


def test_delay():
    # Remove api key for test if it exists
    if "PUBPROXY_API_KEY" in os.environ:
        del os.environ["PUBPROXY_API_KEY"]

    pf1 = ProxyFetcher(exclude_used=False)
    pf2 = ProxyFetcher(exclude_used=False)

    # And a premium `ProxyFetcher` that has an API key
    os.environ["PUBPROXY_API_KEY"] = "<key>"
    premium_pf = ProxyFetcher(exclude_used=False)

    with patch.object(requests, "get", return_value=MOCK_RESP):
        _ = pf1.get_proxy()

        # Make sure there is a delay for the same one
        start = dt.now()
        pf1.drain()
        _ = pf1.get_proxy()
        assert (dt.now() - start).total_seconds() > 1.0

        # Even in the middle of other `ProxyFetcher`s getting rate limited the
        # premium one should have no delay
        start = dt.now()
        premium_pf.drain()
        _ = premium_pf.get_proxy()
        assert (dt.now() - start).total_seconds() < 0.1

        # Even though it's a separate `ProxyFetcher` the delay should be
        # coordinated
        start = dt.now()
        _ = pf2.get_proxy()
        assert (dt.now() - start).total_seconds() > 1.0


def test_params():
    # Test base params
    if "PUBPROXY_API_KEY" in os.environ:
        del os.environ["PUBPROXY_API_KEY"]
    assert ProxyFetcher()._params == {"limit": 5, "format": "json"}

    # Test premium params from API key
    os.environ["PUBPROXY_API_KEY"] = "<key>"
    assert ProxyFetcher()._params == {
        "limit": 20,
        "format": "json",
        "api": "<key>",
    }

    # Check that going out of bounds is a no no
    with pytest.raises(AssertionError):
        _ = ProxyFetcher(last_checked=0)

    # Same with choosing an incorrect option
    with pytest.raises(AssertionError):
        # Fat-fingered
        _ = ProxyFetcher(level="eilte")

    # `countries` and `not_countries` are incompatilbe
    with pytest.raises(AssertionError):
        _ = ProxyFetcher(countries="US", not_countries=["CA", "NK"])

    # And now it's time to check everything
    before_params = {
        "api_key": "<other key>",
        "level": "elite",
        "protocol": "http",
        "countries": "CA",
        "last_checked": 1,
        "port": 1234,
        "time_to_connect": 2,
        "cookies": True,
        "google": False,
        "https": True,
        "post": False,
        "referer": True,
        "user_agent": False,
    }
    after_params = {
        "api": "<other key>",
        "level": "elite",
        "type": "http",
        "country": "CA",
        "last_check": 1,
        "port": 1234,
        "speed": 2,
        "cookies": True,
        "google": False,
        "https": True,
        "post": False,
        "referer": True,
        "user_agent": False,
        "format": "json",
        "limit": 20,
    }
    assert ProxyFetcher(**before_params)._params == after_params


# FIXME: look at the reason vv
@pytest.mark.skip(
    reason="Should work, but the libary checks for duplicates too early"
)
def test_blacklist():
    pf1 = ProxyFetcher()
    pf2 = ProxyFetcher()

    with patch.object(requests, "get", return_value=MOCK_RESP):
        # So becuase the blacklist is coordinated between the `ProxyFetcher`s
        # even though `pf1` and `pf2` will get the same proxies, they should
        # only return a single unique list between the both of them
        assert {
            pf1.get_proxy(),
            pf2.get_proxy(),
            pf1.get_proxy(),
            pf2.get_proxy(),
            pf1.get_proxy(),
        } == set(PROXIES)


@pytest.mark.skip(reason="unimplemented")
def test_methods():
    pass