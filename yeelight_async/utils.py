def intrange(a, b=None):
    def _func(x):
        if b is None:
            return max(a, int(x))
        return max(a, min(int(x), b))
    return _func

