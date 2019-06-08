class ProxyError(Exception):
    pass


class APIKeyError(ProxyError):
    pass


class RateLimitError(ProxyError):
    pass


class DailyLimitError(ProxyError):
    pass
