"""Trusted synthetic transfer module for offline mechanism checks only."""


def encode(n):
    return b'x' * (3 * n + 2)


def packet_a(packet):
    if len(packet) > 17:
        raise ValueError('capacity')
    return len(packet)


def packet_b(packet):
    if len(packet) > 13:
        raise ValueError('capacity')
    return len(packet)


def unused_consumer(packet):
    if len(packet) > 7:
        raise ValueError('unused')
    return len(packet)


def first(n):
    if type(n) is not int or not 0 <= n <= 10:
        raise ValueError('input')
    return packet_a(encode(n))


def second(n):
    if type(n) is not int or not 0 <= n <= 10:
        raise ValueError('input')
    return packet_b(encode(n))


def guarded(n):
    if type(n) is not int or not 0 <= n <= 10:
        raise ValueError('input')
    if n <= 5:
        return packet_a(encode(n))
    return len(encode(n))


def tolerated(n):
    if type(n) is not int or not 0 <= n <= 10:
        raise ValueError('input')
    return packet_a(encode(n))


def unreachable(n):
    if type(n) is not int or not 0 <= n <= 10:
        raise ValueError('input')
    if n >= 11:
        return packet_a(encode(n))
    return len(encode(n))
