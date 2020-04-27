#!/usr/bin/env python3
"""DNS lookup utility."""

import logging
import socket
from typing import Any, List, Tuple

logger = logging.getLogger(__name__)

# family, type, proto, canonname, sockaddr
# IPV4 vs. (IPV6)
# sockaddr is: ip_address, port, (flow_info, scope_id)
AddrInfoType = List[Tuple[int, int, int, str, Tuple[Any, ...]]]


def lookup(name, port) -> AddrInfoType:
    """
    Look up a lot of information about a remote address.

    Probably does some sort of DNS query.
    """
    ret = socket.getaddrinfo(name, port)
    return ret


def ip(name: str, port: int = 80) -> str:
    """Get the ip associated with a remote address."""
    return lookup(name, port)[0][4][0]


if __name__ == "__main__":
    things = [lookup("composte.me", 443), lookup("google.com", 443)]

    for thing in things:
        for ahh in thing:
            logger.debug(ahh)
        logger.debug("=================")

    logger.debug("composte.me ==> " + ip("composte.me"))
    logger.debug("google.com  ==> " + ip("google.com"))
