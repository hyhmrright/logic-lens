def check(data, limit=3):
    return helper(data, limit)
def helper(data, limit):
    if len(data) > limit:
        raise ValueError('capacity')
    return data
