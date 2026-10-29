def attach(data, /, suffix=b'!', *, enabled=True, marker=None):
    if marker is not None:
        raise ValueError('marker')
    if enabled:
        return data+suffix
    return data
