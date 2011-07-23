"""Cautious introspector that invokes no properties.

"""
__version__ = '0.1'

# Shortcut so users can `import squit; squint.pdb()` or `squint.set_trace()`.

from pdb import set_trace
pdb = set_trace

# Shortcut that allows `squint.at(obj)`

def at(obj):
    from squint.squinter import Squinter
    return Squinter(obj)
