#!/usr/bin/env python3

import socket


def lookup(name, port):
    """
    Look up a lot information about a remote address. Probably does some sort
    of DNS query.
    """
    ret = socket.getaddrinfo(name, port)
    return ret


def ip(name, port=80):
    """
    Get the ip associated with a remote address
    """
    return lookup(name, port)[0][4][0]


if __name__ == "__main__":
    things = [lookup("composte.me", 443), lookup("google.com", 443)]

    for thing in things:
        for ahh in thing:
            print(ahh)
        print("=================")

    print("composte.me ==> " + ip("composte.me"))
    print("google.com  ==> " + ip("google.com"))
