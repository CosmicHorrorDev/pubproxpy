# TODO: call the super on exception to set the error message in here
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


class ProxyError(Exception):
    """Generic base error
    """


class APIKeyError(ProxyError):
    """Error for incorrect API key response
    """


class RateLimitError(ProxyError):
    """Error for rate limiting response
    """


class DailyLimitError(ProxyError):
    """Error for hitting the daily request limit
    """


class NoProxyError(ProxyError):
    """Error for getting the "No Proxy" response
    """
