from enum import Enum


class Level(Enum):
    ANONYMOUS = "anonymous"
    ELITE = "elite"


class Protocol(Enum):
    HTTP = "http"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
