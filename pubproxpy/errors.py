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
