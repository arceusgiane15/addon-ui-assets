"""Build steps registered by the art / UI modules: fn(out, ctx, log), run in import order."""
STEPS = []


def step(fn):
    STEPS.append(fn)
    return fn
