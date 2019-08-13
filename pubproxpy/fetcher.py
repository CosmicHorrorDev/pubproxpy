#!/usr/bin/env python3
# TODO: update documentation after all changes are made
# TODO: add `exclude_used` to the docs
# TODO: check for error with using a proxy to get proxies
# TODO: Add table of contents to readme
# TODO: Update readme based on new setup
# TODO: `rg` to find any other todos before release
# TODO: specify what params can't be checked for correctness in readme
# TODO: handle case of request failing?
# TODO: mention that rate limiting will still happen from mulitple programs

import requests

from datetime import datetime as dt
import os
from time import sleep
from urllib.parse import urlencode

from .errors import (
    ProxyError,
    APIKeyError,
    RateLimitError,
    DailyLimitError,
    NoProxyError,
    INVALID_API_RESP,
    RATE_LIMIT_RESP,
    DAILY_LIMIT_RESP,
    NO_PROXY_RESP,
)
from .singleton import Singleton


class FetcherShared(metaclass=Singleton):
    """This class is used solely for the purpose of synchronizing request times
    and used lists between different `ProxyFetcher`s to prevent rate limiting
    and reusing old proxies.
    NOTE: This is not thread safe
    """

    def __init__(self):
        self.last_requested = None
        self.used = set()


# TODO: add documentation comments
# TODO: set up tests for things
# TODO: move all the constants for ProxyFetcher outside of the class
class ProxyFetcher:
    _BASE_URI = "http://pubproxy.com/api/proxy?"
    # Parameters used by `ProxyFetcher` for the pubproxy api
    _PARAMS = (
        "api_key",
        "level",
        "protocol",
        "countries",
        "not_countries",
        "last_checked",
        "port",
        "time_to_connect",
        "cookies",
        "google",
        "https",
        "post",
        "referer",
        "user_agent",
    )
    # Parameters that have explicit options
    _PARAM_OPTS = {
        "level": ("anonymous", "elite"),
        "protocol": ("http", "socks4", "socks5"),
    }
    # Parameters that are bounded
    _PARAM_BOUNDS = {"last_checked": (1, 1000), "time_to_connect": (1, 60)}

    # Request delay for keyless request limiting in seconds
    # Note: Requests are supposed to be limited to 1 per second, but you are
    #       sometimes rate limited when using 1.0 so 1.05 was picked
    _REQUEST_DELAY = 1.05

    def __init__(self, *, exclude_used=True, **params):
        self._exclude_used = exclude_used

        # Setup `_params` and `_query`
        self._params = self._setup_params(params)
        self._query = f"{self._BASE_URI}{urlencode(self._params)}"

        # List of unused proxies to give
        self._proxies = []

        # Shared data between `ProxyFetcher`s, includes request time and used
        # list (used list only used if `exclude_used` is True)
        self._shared = FetcherShared()

    def _setup_params(self, params):
        self._verify_params(params)

        # Try to read api key from environment if not provided
        if "api_key" not in params and "PUBPROXY_API_KEY" in os.environ:
            params["api_key"] = os.environ["PUBPROXY_API_KEY"]

        params = self._rename_params(params)
        return self._format_params(params)

    def _verify_params(self, params):
        # `countries` and `not_countries` are mutually exclusive
        assert "countries" not in params or "not_countries" not in params, (
            'incompatible parameters, "countries" and "not_countries" are'
            " mutually exclusive"
        )

        # Verify all params are valid, and satisfy the valid bounds or options
        for param, val in params.items():
            assert param in self._PARAMS, (
                f'invalid parameter "{param}" valid parameters are'
                f" {[p for p in self._PARAMS]}"
            )

            if param in self._PARAM_OPTS:
                opts = self._PARAM_OPTS[param]
                assert (
                    val in opts
                ), f'invalid value "{val}" for "{param}" options are {opts}'

            if param in self._PARAM_BOUNDS:
                low, high = self._PARAM_BOUNDS[param]
                assert (
                    low <= val <= high
                ), f'value "{val}" for "{param}" out of bounds ({low}, {high})'

    def _rename_params(self, params):
        """Method to rename some params from the API's method to pubproxy's
        since some of the names are confusing / unclear
        """
        translations = (
            ("api_key", "api"),
            ("protocol", "type"),
            ("countries", "country"),
            ("not_countries", "not_country"),
            ("last_checked", "last_check"),
            ("time_to_connect", "speed"),
        )

        for before, after in translations:
            if before in params:
                params[after] = params[before]
                del params[before]

        return params

    def _format_params(self, params):
        params["format"] = "txt"
        if "api" in params:
            params["limit"] = 20
        else:
            params["limit"] = 5

        # Join country and not_country by comma if it's a list or tuple
        # TODO: is this already done by formatting as a url?
        if "country" in params:
            if isinstance(params["country"], (list, tuple)):
                params["country"] = ",".join(params["country"])
        elif "not_country" in params:
            if isinstance(params["not_country"], (list, tuple)):
                params["not_country"] = ",".join(params["not_country"])

        return params

    # TODO: can't this be simplified down to a `return self.get_proxies(1)[0]`?
    # TODO: update doc comment
    def get_proxy(self):
        """Attempt to get a proxy matching specified params, used proxies are
        added to a blacklist if `exclude_used is True` to prevent reuse
        """
        # Get new proxies if none remain
        while not self._proxies:
            self._fetch()

        # Add proxy to blacklist if `_exclude_used`, then return
        proxy = self._proxies.pop()
        if self._exclude_used:
            self._shared.used.add(proxy)

        return proxy

    # TODO: add doc comment
    def get_proxies(self, amount):
        # Get new proxies till there is enough for amount
        while len(self._proxies) < amount:
            self._fetch()

        # Store the deisred proxies in temp and remove from list
        temp = self._proxies[:amount]
        self._proxies = self._proxies[amount:]

        # Add the proxies to the blacklist if `_exclude_used`
        if self._exclude_used:
            self._shared.used |= set(temp)

        return temp

    # TODO: this should return the proxies instead of automatically adding them
    def _fetch(self):
        """Attempts to get the proxies from pubproxy.com and adds them to
        `self._proxies`, will `sleep` to prevent getting rate-limited
        """
        # Limit number of requests to 1 per `self._REQUEST_DELAY` unless an api
        # key is provided
        last_time = self._shared.last_requested
        if last_time is not None and "api" not in self._params:
            delta = (dt.now() - last_time).total_seconds()
            if delta < self._REQUEST_DELAY:
                sleep(self._REQUEST_DELAY - delta)
        self._shared.last_requested = dt.now()

        # Query the api
        resp = requests.get(self._query)

        # Raise the correct error if the response isn't valid
        if not self._valid_resp(resp.text):
            if resp.text == INVALID_API_RESP:
                raise APIKeyError(
                    "Invalid API key, make sure you're using a valid API key"
                )
            elif resp.text == RATE_LIMIT_RESP:
                # TODO: add a comment saying to open an issue on the repo
                #       if they got this error while using the default
                #       delay
                raise RateLimitError("You have exceeded the rate limit")
            elif resp.text == DAILY_LIMIT_RESP:
                raise DailyLimitError("You have exceeded the daily limit")
            elif resp.text == NO_PROXY_RESP:
                raise NoProxyError(
                    "No proxies were found using these parameters"
                    "  consider broadening these params\nParams:{self._params}"
                )
            else:
                raise ProxyError(
                    # TODO: add link to github repo?
                    "There was an unknown response, please report the issue"
                    f'\nResponse text: "{resp.text}"'
                )

        # Update with the new proxies
        proxies = set(resp.text.split("\n"))
        # Remove any that were already used and update current list
        if self._exclude_used:
            proxies -= self._shared.used

        self._proxies += proxies

    # TODO: add doc comment
    # TODO: this could likely be simplified by switching to json, strongly
    #       consider doing this later, this could also be used to verify that
    #       both `countries` and `not_countries` are correct
    def _valid_resp(self, resp):
        if not resp:
            return False

        for proxy in resp.split("\n"):
            if not self._valid_proxy(proxy):
                return False

        return True

    # TODO: add doc comment
    def _valid_proxy(self, proxy):
        try:
            ip, port = proxy.split(":")
            port = int(port)

            parts = ip.split(".")
            assert len(parts) == 4  # 4 bytes for ipv4
            for part in parts:
                part = int(part)
                assert 0 <= part <= 255  # Outside byte range
        except (AssertionError, ValueError):
            return False

        return True
