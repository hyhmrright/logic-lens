"""Trusted synthetic program; no normative validity intervals inferred from code."""
__all__ = ['hidden', 'converted', 'multiple', 'alternate', 'permitted', 'conflicting', 'impossible', 'dynamic']


def _hidden(x):
    if x == 23:
        raise ValueError('interior path')
    return x


def hidden(n):
    return _hidden(3*n+2)


def _route(x):
    if 15 < x:
        if x < 30:
            return _hidden(x)
    return x


def converted(n):
    return _route(n*3+2)


def _sink(data):
    if len(data) > 10:
        raise ValueError('capacity')
    return len(data)


def multiple(n):
    if n < 5:
        return _sink(b'x'*n)
    return _sink(b'x'*(2*n))


def alternate(n):
    if n > 5:
        return n
    return _sink(b'x'*n)


def permitted(n):
    return _sink(b'x'*(2*n))


def conflicting(n):
    return n


def impossible(n):
    if n < 4:
        if n > 12:
            return _hidden(n)
    return n


def dynamic(n):
    return globals()['hidden'](n)
