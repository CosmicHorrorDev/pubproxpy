_REPO_URL = "https://github.com/LovecraftianHorror/pubproxpy"

INVALID_API_RESP = (
    "Invalid API. Get your API to make unlimited requests at"
    "  http://pubproxy.com/#premium"
)
RATE_LIMIT_RESP = (
    "We have to temporarily stop you. You're requesting proxies a little"
    " too fast (2+ requests per second). Get your API to remove this limit"
    " at http://pubproxy.com/#premium"
)
DAILY_LIMIT_RESP = (
    "You have reached the maximum 50 requests for today. Get your API to"
    " make unlimited requests at http://pubproxy.com/#premium"
)
NO_PROXY_RESP = "No proxy"

_PROXY_ERROR_MESSAGE = (
    f"There was an unknown response, consider raising an issue at {_REPO_URL}"
)
_API_KEY_ERROR_MESSAGE = (
    "Invalid API key, make sure you're using a valid API key"
)
_RATE_LIMIT_ERROR_MESSAGE = (
    "You have exceeded the rate limit, this could be due to multiple programs"
    "/threads with a `ProxyFetcher` all attempting to use the API within the"
    " time limit, or from using multiple `ProxyFetcher`s with at least one"
    " having `exclude_used` set to `False`. If none of these are the case then"
    f" sorry but the API hates you, consider raising an issue at {_REPO_URL}"
)
_DAILY_LIMIT_ERROR_MESSAGE = "You have exceeded the daily limit :/"
_NO_PROXY_ERROR_MESSAGE = (
    "No proxies were found, consider broadening the parameters used"
)


class ProxyError(Exception):
    """Generic base error"""

    def __init__(self, response, message=_PROXY_ERROR_MESSAGE):
        if response is None:
            super().__init__(message)
        else:
            super().__init__(f"{message}\nResponse text: {response.text}")


class APIKeyError(ProxyError):
    """Error for incorrect API key response"""

    def __init__(self, message=_API_KEY_ERROR_MESSAGE):
        super().__init__(None, message)


class RateLimitError(ProxyError):
    """Error for rate limiting response"""

    def __init__(self, message=_RATE_LIMIT_ERROR_MESSAGE):
        super().__init__(None, message)


class DailyLimitError(ProxyError):
    """Error for hitting the daily request limit"""

    def __init__(self, message=_DAILY_LIMIT_ERROR_MESSAGE):
        super().__init__(None, message)


class NoProxyError(ProxyError):
    """Error for getting the "No Proxy" response"""

    def __init__(self, message=_NO_PROXY_ERROR_MESSAGE):
        super().__init__(None, message)


API_ERROR_MAP = {
    INVALID_API_RESP: APIKeyError,
    RATE_LIMIT_RESP: RateLimitError,
    DAILY_LIMIT_RESP: DailyLimitError,
    NO_PROXY_RESP: NoProxyError,
}
