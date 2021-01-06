import requests

from datetime import datetime as dt
import json
import os
from time import sleep
from urllib.parse import urlencode
from warnings import warn

from pubproxpy._singleton import Singleton
from pubproxpy.errors import ProxyError, API_ERROR_MAP
from pubproxpy.types import Level, Protocol


class _FetcherShared(metaclass=Singleton):
    """This class is used solely for the purpose of synchronizing request times
    and used lists between different `ProxyFetcher`s to prevent rate limiting
    and reusing old proxies.
    NOTE: This does not synchronize between threads
    """

    def __init__(self):
        self.last_requested = None
        self.used = set()

    def reset(self):
        self.__init__()


class ProxyFetcher:
    """Class used to fetch proxies from the pubproxy API matching the provided
    parameters
    """

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

    # Parameters that are bounded
    _PARAM_BOUNDS = {"last_checked": (1, 1000), "time_to_connect": (1, 60)}

    # Request delay for keyless request limiting in seconds
    # Note: Requests are supposed to be limited to 1 per second, but 1.0 and
    #       1.01 sometimes still triggers the rate limit so 1.05 was picked
    _REQUEST_DELAY = 1.05

    def __init__(self, *, exclude_used=True, **params):
        self._exclude_used = exclude_used

        # Setup `_params` and `_query`
        self._params = self._setup_params(params)
        self._query = f"{self._BASE_URI}{urlencode(self._params)}"

        # List of unused proxies to give
        self._proxies = []

        # Shared data between `ProxyFetcher`s, includes request time and used
        # list (used list only used if `exclude_used` is `True`)
        self._shared = _FetcherShared()

    def _setup_params(self, params):
        """Checks all of the params and renames to acutally work with the API"""

        self._verify_params(params)

        if "api_key" in params and "PUBPROXY_API_KEY" in os.environ:
            warn(
                "The library will be changing the precendence on overriding the API key"
                " when it's present as both a parameter and env var. This involves a"
                " breaking change (hence the warning) More information is available in"
                " this issue"
                " https://github.com/LovecraftianHorror/pubproxpy/issues/11"
            )

        # Try to read api key from environment if not provided
        if "api_key" not in params and "PUBPROXY_API_KEY" in os.environ:
            params["api_key"] = os.environ["PUBPROXY_API_KEY"]

        params = self._rename_params(params)
        return self._format_params(params)

    def _verify_params(self, params):
        """Since the API really lets anything go, check to make sure params are
        compatible with each other, within the bounds, and are one of the
        accepted options
        """

        # `countries` and `not_countries` are mutually exclusive
        if "countries" in params and "not_countries" in params:
            raise ValueError(
                "incompatible parameters, `countries` and `not_countries` are"
                " mutually exclusive"
            )

        # Check that protocol and level are the correct type
        for key, enum_type in (("protocol", Protocol), ("level", Level)):
            if key in params:
                val = params[key]
                if not isinstance(val, enum_type):
                    raise ValueError(
                        f"{key} should be of type `{enum_type}` not "
                        f" `{type(val)}`"
                    )

        # Verify all params are valid, and satisfy the valid bounds or options
        for param, val in params.items():
            if param not in self._PARAMS:
                raise ValueError(
                    f'unrecognized parameter "{param}" valid parameters are'
                    f" {[p for p in self._PARAMS]}"
                )

            if param in self._PARAM_BOUNDS:
                low, high = self._PARAM_BOUNDS[param]
                if val < low or val > high:
                    raise ValueError(
                        f'value "{val}" for "{param}" out of bounds'
                        f" ({low} to {high})"
                    )

    def _rename_params(self, params):
        """Method to rename some params from the API's method to pubproxy's
        since some of the API's names are confusing / unclear
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
        """Set any of the always used params and make sure everything is
        `urlencode`able
        """

        # Parameters kept outside of the user's control
        params["format"] = "json"
        if "api" in params:
            params["limit"] = 20
        else:
            params["limit"] = 5

        # Join country and not_country by comma if it's a list or tuple
        if "country" in params:
            if isinstance(params["country"], (list, tuple)):
                params["country"] = ",".join(params["country"])
        elif "not_country" in params:
            if isinstance(params["not_country"], (list, tuple)):
                params["not_country"] = ",".join(params["not_country"])

        # Get value from enums
        for key in ("level", "type"):
            if key in params:
                params[key] = params[key].value

        return params

    def drain(self):
        """Returns any proxies remaining in the current list"""
        return self.get(len(self._proxies))

    def get(self, amount=1):
        """Attempts to get `amount` proxies matching the specified params"""
        # Remove any blacklisted proxies from the internal list
        # Note: this needs to be done since reused proxies can sit in the
        #       internal list of separate `ProxyFetcher`s
        if self._exclude_used:
            self._proxies = [
                p for p in self._proxies if p not in self._shared.used
            ]

        # Get enough proxies to satisfy `amount`
        while len(self._proxies) < amount:
            self._proxies += self._fetch()

        # Store the deisred proxies in `temp` and remove from `self._proxies`
        temp = self._proxies[:amount]
        self._proxies = self._proxies[amount:]

        # Add the proxies to the blacklist if `_exclude_used`
        if self._exclude_used:
            self._shared.used |= set(temp)

        return temp

    def _fetch(self):
        """Attempts to get the proxies from pubproxy.com, will `sleep` to
        prevent getting rate-limited
        """

        # Limit number of requests to 1 per `self._REQUEST_DELAY` unless an API
        # key is provided
        last_time = self._shared.last_requested
        if last_time is not None and "api" not in self._params:
            delta = (dt.now() - last_time).total_seconds()
            if delta < self._REQUEST_DELAY:
                sleep(self._REQUEST_DELAY - delta)
        self._shared.last_requested = dt.now()

        # Query the api
        resp = requests.get(self._query)

        if not resp.ok:
            warn(
                "The library will be changing how API errors are exposed, so that the"
                " different conditions are expressed with different error classes. This"
                " will be a breaking change (hence the warning). More information is"
                " available in this issue"
                " https://github.com/LovecraftianHorror/pubproxpy/issues/11"
            )
        # And ensure the response is ok
        resp.raise_for_status()

        try:
            data = json.loads(resp.text)["data"]
        except json.decoder.JSONDecodeError:
            raise API_ERROR_MAP.get(resp.text) or ProxyError(resp)

        # Get the returned list of proxies
        proxies = set([d["ipPort"] for d in data])

        # Remove any that were already used and update current list
        if self._exclude_used:
            proxies -= self._shared.used

        return proxies
