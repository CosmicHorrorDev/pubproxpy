#!/usr/bin/env python3

import requests

from datetime import datetime as dt
import os
from time import sleep
from urllib.parse import urlencode

from .errors import ProxyError, APIKeyError, RateLimitError, DailyLimitError
from .singleton import Singleton


class FetcherShared(metaclass=Singleton):
    """This class is used solely for the purpose of synchronizing request times
    between different `ProxyFetcher`s to prevent rate limiting. NOTE: This is
    not thread safe
    """

    def __init__(self):
        self.last_requested = None


# TODO: add documentation comments
# TODO: set up tests for things
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
    _REQUEST_DELAY = 1.0

    # All the error messages that are matched against
    _INVALID_API_RESP = (
        "Invalid API. Get your API to make unlimited requests at"
        "  http://pubproxy.com/#premium"
    )
    _RATE_LIMIT_RESP = (
        "We have to temporarily stop you. You're requesting proxies a little"
        " too fast (2+ requests per second). Get your API to remove this limit"
        " at http://pubproxy.com/#premium"
    )
    _DALY_LIMIT_RESP = (
        "You have reached the maximum 50 requests for today. Get your API to"
        " make unlimited requests at http://pubproxy.com/#premium"
    )

    def __init__(self, **params):
        # Setup `_params` and `_query`
        self._params = self._setup_params(params)
        self._query = f"{self._BASE_URI}{urlencode(self._params)}"

        # Internal list and set used to store new and used proxies
        self._proxies = []
        self._used = set()

        # Used to prevent rate limiting
        self._shared_time = FetcherShared()

    def set_params(self, **params):
        # Setup `_params` and `_query`
        self._params = self._setup_params(params)
        self._query = f"{self._BASE_URI}{urlencode(self._params)}"

        # Clear the current proxy list
        self._proxies = []

    def update_params(self, **new_params):
        # Update `_params` and `_query`
        new_params = self._setup_params(new_params)

        # Special case to keep `country` and `not_country` separate
        if "country" in new_params and "not_country" in self._params:
            del self._params["not_country"]
        elif "not_country" in new_params and "country" in self._params:
            del self._params["country"]

        for param, val in new_params.items():
            self._params[param] = val
        self._query = f"{self._BASE_URI}{urlencode(self._params)}"

        # Clear the current proxy list
        self._proxies = []

    def clear_params(self, *remove_params):
        for param in remove_params:
            assert param in self._PARAMS, (
                f'invalid parameter "{param}" valid parameters are'
                f" {[p for p in self._PARAMS]}"
            )
            del self._params[param]

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
        params["limit"] = 5

        # Join country and not_country by comma if it's a list or tuple
        if "country" in params:
            if isinstance(params["country"], (list, tuple)):
                params["country"] = ",".join(params["country"])
        elif "not_country" in params:
            if isinstance(params["not_country"], (list, tuple)):
                params["not_country"] = ",".join(params["not_country"])

        return params

    def get_proxy(self):
        """Attempt to get a proxy specified by the parameters set in `__init__`
        or `set_params`, used proxies are added to a blacklist to prevent
        reuse
        """
        # Get new proxies if none remain
        while not self._proxies:
            self._fetch()

        # Add proxy to blacklist, then return
        proxy = self._proxies.pop()
        self._used.add(proxy)
        return proxy

    def get_proxies(self, amount):
        # Get new proxies till there is enough for amount
        while len(self._proxies) < amount:
            self._fetch()

        # Store the deisred proxies, remove, then return
        temp = self._proxies[:amount]
        self._proxies = self._proxies[amount:]
        return temp

    def _fetch(self):
        """Attempts to get the proxies from `pubproxy.com` and adds them to
        `self._proxies`
        """
        # Limit number of requests to 1 per second unless api key given
        last_time = self._shared_time.last_requested
        if last_time is not None and "api" not in self._params:
            delta = (dt.now() - last_time).total_seconds()
            if delta < self._REQUEST_DELAY:
                sleep(self._REQUEST_DELAY - delta)
        self._shared_time.last_requested = dt.now()

        # Query the api
        resp = requests.get(self._query)

        # TODO: check these against a regex to see if they match a proxy
        # Check the response against any errors
        if resp.text == self._INVALID_API_RESP:
            raise APIKeyError(
                "Invalid API key, make sure you're using a valid API key"
            )
        elif resp.text == self._RATE_LIMIT_RESP:
            raise RateLimitError("You have exceeded the rate limit")
        elif resp.text == self._DALY_LIMIT_RESP:
            raise DailyLimitError("You have exceeded the daily limit")

        # Update with the new proxies
        proxies = set(resp.text.split("\n"))
        # Remove any that were already used and update current list
        proxies -= self._used
        self._proxies += proxies
