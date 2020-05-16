import pytest
import requests

from datetime import datetime as dt
import json
from unittest.mock import patch

from pubproxpy import ProxyFetcher


# FIXME: actually mock the request itself
class _mock_resp:
    def __init__(self, text):
        self.text = text


MOCK_RESP = _mock_resp(
    json.dumps(
        {
            "data": [
                {"ipPort": "0.0.0.0:0000"},
                {"ipPort": "1.1.1.1:1111"},
                {"ipPort": "2.2.2.2:2222"},
                {"ipPort": "3.3.3.3:33333"},
                {"ipPort": "4.4.4.4:4444"},
            ]
        }
    )
)


def test_delay():
    pf1 = ProxyFetcher(exclude_used=False)
    pf2 = ProxyFetcher(exclude_used=False)

    with patch.object(requests, "get", return_value=MOCK_RESP):
        _ = pf1.get_proxy()

        # Make sure there is a delay for the same one
        start = dt.now()
        pf1.drain()
        _ = pf1.get_proxy()
        assert (dt.now() - start).total_seconds() > 1.0

        # Even though it's a separate `ProxyFetcher` the delay should be
        # coordinated
        start = dt.now()
        _ = pf2.get_proxy()
        assert (dt.now() - start).total_seconds() > 1.0


@pytest.mark.skip(reason="unimplemented")
def test_params():
    pass


@pytest.mark.skip(reason="unimplemented")
def test_blacklist():
    pass


@pytest.mark.skip(reason="unimplemented")
def test_methods():
    pass
