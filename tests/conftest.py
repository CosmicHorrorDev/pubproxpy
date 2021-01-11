import os
from typing import Generator

import pytest
from httmock import HTTMock, all_requests  # type: ignore

from pubproxpy.fetcher import _FetcherShared


@pytest.fixture(autouse=True)
def _cleanup() -> Generator[None, None, None]:
    # Remove any possibly preexisting key
    if "PUBPROXY_API_KEY" in os.environ:
        del os.environ["PUBPROXY_API_KEY"]

    yield  # <-- The test runs here

    # Cleanup up the shared junk from the `Singleton` (also note that this is
    # one of the pains of using a singleton)
    _FetcherShared().reset()


@all_requests
def _fail_all(url, request) -> None:
    raise Exception(
        f"Attempted to actually request {url} with {request} without mocking"
    )


@pytest.fixture(autouse=True)
def dont_really_request_api() -> Generator[None, None, None]:
    with HTTMock(_fail_all):
        yield
