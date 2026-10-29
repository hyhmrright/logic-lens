"""Synthetic transport: n is a count of records, wire size is measured in bytes.
The public transfer operation accepts every integer n from 0 through 10.
A separately declared restrictive policy forbids n from 6 through 10.
The packet consumer requires a packet of at most 17 bytes.
"""


def encode(n):
    return b'x' * (3 * n + 2)


def consume(packet):
    if len(packet) > 17:
        raise ValueError('packet exceeds capacity')
    return len(packet)


def transfer(n):
    if type(n) is not int or not 0 <= n <= 10:
        raise ValueError('outside public domain')
    return consume(encode(n))


def routed_transfer(n):
    if type(n) is not int or not 0 <= n <= 10:
        raise ValueError('outside public domain')
    if n <= 5:
        return consume(encode(n))
    # A separate route has no single-packet capacity requirement.
    return len(encode(n))


def secondary_consume(packet):
    if len(packet) > 17:
        raise ValueError('second capacity check')
    return len(packet)


def unreachable_transfer(n):
    if type(n) is not int or not 0 <= n <= 10:
        raise ValueError('outside public domain')
    if 11 <= n <= 20:
        return consume(encode(n))
    return len(encode(n))
