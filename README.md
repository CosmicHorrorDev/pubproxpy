# Pubproxpy

An easy to use Python wrapper for [pubproxy](http://pubproxy.com)'s public proxy API.

## Installation

Install the pybproxpy package using your standard Python package manager e.g.

```bash
$ pip install pubproxpy
```

## Keyless API Limitations

### API Daily Limits

At the time of writing this, without an API key the pubproxy API limits users to 5 proxies per request and 50 requests per day. The maximum proxies per request is always used to minimize rate limiting along with getting the most proxies possible within the request limit.

### API Rate Limiting

Without an API key pubproxy limits users to one request per second so a `ProxyFetcher` will try to ensure that at most only one request per second is done without an API key. This is synchronized between `ProxyFetcher`s, but this is not thread safe so make sure all `ProxyFetcher`s are on the same thread if you have no API key. The rate limiting is quite severe, upon being hit the API seems to deny requests for several minutes/hours.

## Quickstart Example

```python
from pubproxpy import ProxyFetcher

# ProxyFetcher for proxies that support https, are elite anonymity level,
# and connected in 15 seconds or less
http_pf = ProxyFetcher(protocol="http", https=True, level="elite",
                       time_to_connect=15)

# ProxyFetcher for proxies that use the socks5 protocol, are located in
# the US or Canada and support POST requests
socks_pf = ProxyFetcher(protocol="socks5", countries=["US", "CA"], post=True)

# Get and print 10 of each kind of proxy, even though there are multiple
# `ProxyFetcher`s, the delays will be coordinated to prevent rate limiting
for _ in range(10):
    https_proxy = http_pf.get_proxy()
    socks_proxy = socks_pf.get_proxy()

    # Do something with the proxies, like spawn worker threads that use them
```

### Advanced Example

```python
from pubproxpy import ProxyFetcher

# Get a single elite proxy from France
pf = ProxyFetcher(level="elite", countries="FR")
elite_proxy = pf.get_proxy()

# Now get 20 elite proxies from anywhere except France and Ireland that support
# post requests
# NOTE: setting `not_countries` will remove `countries` since they're
#       incompatible
pf.update_params(post=True, not_countries=["FR", "IE"])
anon_proxies = pf.get_proxies(20)
```

## Documentation

Getting proxies is fully handled by the `ProxyFetcher` class. There are several parameters you can pass on initialization, by using `set_params`, or by using `update_params` to narrow down the proxies to a suitable range. From there you can just call `get_proxy` to receive a proxy in the form of `{ip-address}:{port-number}` or call `get_proxies(amount)` to receive a list of `amount` proxies. Also there is an internal blacklist to ensure that the same proxy ip and port combo will not be used more than once per `ProxyFetcher`.

### `ProxyFetcher` Parameters

|Parameter|Type|Description|
|:--|:--|:--|
|`api_key`|`int`|API key for a paid account, you can also set `$PUBPROXY_API_KEY` to pass your key, passing the `api_key` parameter will override this|
|`level`|`str`|[Options: anonymous, elite] Proxy anonymity level|
|`protocol`|`str`|[Options: http, socks4, socks5] The proxy protocol|
|`countries`|`str` or `list<str>`|locations of the proxy using the [ISO-3166 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code, **Incompatible with `not_countries`**|
|`not_countries`|`str` or `list<str>`|blacklist locations of the proxy using the [ISO-3166 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code, **Incompatible with `countries`**|
|`last_checked`|`int`|[Bounds: 1-1000] Minutes since the proxy was checked|
|`port`|`int`|Proxies using a specific port|
|`time_to_connect`|`int`|[Bounds: 1-60] How many seconds it took for the proxy to connect|
|`cookies`|`bool`|Supports requests with cookies|
|`google`|`bool`|Can connect to Google|
|`https`|`bool`|Supports https requests|
|`post`|`bool`|Supports post requests|
|`referer`|`bool`|Supports referer requests|
|`user_agent`|`bool`|Supports user-agent requests|
