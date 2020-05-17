# Pubproxpy

An easy to use Python wrapper for [pubproxy](http://pubproxy.com)'s public proxy API.

## Installation

**NOTE:** The minimum python version for this library is 3.7, check with `python -V` or `python3 -V` if you're unsure about your current version.

Install the [pubproxpy](https://pypi.org/project/pubproxpy/) package using your standard Python package manager e.g.

```bash
$ pip install pubproxpy
```

As always you are recommended to install into a virtual environment.

## Keyless API Limitations

### API Daily Limits

At the time of writing this without an API key the pubproxy API limits users to 5 proxies per request and 50 requests per day. The maximum proxies per request is always used to minimize rate limiting along with getting the most proxies possible within the request limit meaning you should get 250 proxies per day without needing an API key.

### API Rate Limiting

Without an API key pubproxy limits users to one request per second so a `ProxyFetcher` will try to ensure that at most only one request per second is done without an API key. This is synchronized between `ProxyFetcher`s, but this is not thread safe so make sure all `ProxyFetcher`s are on one thread in one program if you have no API key. The rate limiting is quite severe, so upon being hit the API seems to deny requests for several minutes/hours.

## Quickstart Example

```python
from pubproxpy import Level, Protocol, ProxyFetcher

# ProxyFetcher for proxies that use the socks5 protocol, are located in
# the US or Canada and support POST requests
socks_pf = ProxyFetcher(
    protocol=Protocol.SOCKS5, countries=["US", "CA"], post=True
)

# ProxyFetcher for proxies that support https, are elite anonymity level,
# and connected in 15 seconds or less
https_pf = ProxyFetcher(
    protocol=Protocol.HTTP, https=True, level=Level.ELITE, time_to_connect=15
)

# Get one socks proxy, followed by 10 https proxies
# NOTE: even though there are multiple `ProxyFetcher`s the delays are
#       coordinated between them to prevent rate limiting
socks_proxy = socks_pf.get()[0]  # Get a single socks proxy
https_proxies = https_pf.get(10)  # Get a 10 https proxies

# And then if you want to get any remaining proxies left over before you're
# done you can!
unused_proxies = socks_pf.drain()

# Do something with the proxies, like spawn worker threads that use them
```

## Documentation

Getting proxies is handled by the `ProxyFetcher` class. There are several parameters you can pass on initialization to narrow down the proxies to a suitable type. From there you can just call `.get(amount=1)` to receive a list of `amount` proxies where each proxy is in the form of `"{ip}:{port}"`. There is an internal blacklist to ensure that the same proxy IP and port combo will not be used more than once by any `ProxyFetcher`, unless `exclude_used` is `False`.

### `ProxyFetcher` Parameters

Since the API doesn't check pretty much anything for correctness, we do our best in the `ProxyFetcher` to ensure nothing is wrong. As far as I know the only thing that isn't checked is that the `countries` or `not_countries` actually use the correct codes.

|Parameter|Type|Description|
|:--|:--|:--|
|`exclude_used`|`bool` |[_Default: `True`_] If the `ProxyFetcher` should prevent re-returning proxies|
|`api_key`|`str`|API key for a paid account, you can also set `$PUBPROXY_API_KEY` to pass your key, passing the `api_key` parameter will override the env-var if both are present|
|`level`|`pubproxpy.Level`|[_Options: `ANONYMOUS`, `ELITE`_] Proxy anonymity level|
|`protocol`|`pubproxpy.Protocol`|[_Options: `HTTP`, `SOCKS4`, `SOCKS5`_] Desired communication protocol|
|`countries`|`str` or `list<str>`|Locations of the proxy using the [ISO-3166 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code, **Incompatible with `not_countries`**|
|`not_countries`|`str` or `list<str>`|Blacklist locations of the proxy using the [ISO-3166 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code, **Incompatible with `countries`**|
|`last_checked`|`int`|[_Bounds: 1-1000_] Minutes since the proxy was checked|
|`port`|`int`|Proxies using a specific port|
|`time_to_connect`|`int`|[_Bounds: 1-60_] How many seconds it took for the proxy to connect|
|`cookies`|`bool`|Supports requests with cookies|
|`google`|`bool`|Can connect to Google|
|`https`|`bool`|Supports HTTPS requests|
|`post`|`bool`|Supports POST requests|
|`referer`|`bool`|Supports referer requests|
|`user_agent`|`bool`|Supports forwarding user-agents|

### `ProxyFetcher` Methods

Keeping it simple (stupid), so just `.get(amount=1)` and `.drain()`.

|Method|Returns|
|:--|:--|
|`.get(amount=1)`|List of `amount` proxies, where each proxy is a `str` in the form `"{ip}:{port}"`|
|`.drain()`|Returns any proxies remaining in the current list, useful if you are no longer getting proxies and want to save any left over|

### Exceptions

All the exceptions are defined in `pubproxpy.errors`.

|Exception|Description|
|:--|:--|
|`ProxyError`|Base exception that all other pubproxpy errors inherit from, also raised when the API returns an unknown response|
|`APIKeyError`|Error raised when the API gives an incorrect API Key response|
|`RateLimitError`|Error raised when the API gives a rate-limiting response (more than 1 request per second)|
|`DailyLimitError`|Error raised when the API gives the daily request limit response|

