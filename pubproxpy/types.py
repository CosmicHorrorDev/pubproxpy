from enum import Enum
from typing import Dict, List, NewType, Union


class Level(Enum):
    ANONYMOUS = "anonymous"
    ELITE = "elite"


class Protocol(Enum):
    HTTP = "http"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


ParamTypes = Union[bool, int, str, List[str], Level, Protocol]
Params = Dict[str, ParamTypes]
Proxy = NewType('Proxy', str)
