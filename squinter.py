"""Squinter that lets you examine live Python objects."""

_unknown = object()

class Squinter(object):

    def __init__(self, obj):
        self._obj = obj
        self.refs = None

    # Discovering and delivering referenced objects.

    def load(self):
        """Load referenced objects, if we have not done so already."""
        if self.refs is None:
            self.reload()

    def reload(self):
        """Rebuild our collection of referenced objects."""
        self.refs = dict(iter_refs(self._obj))

    def __getattr__(self, name):
        """Return a referenced object, wrapped in a new Squinter."""
        self.load()
        value = self.refs.get(name, _unknown)
        if value is not _unknown:
            return Squinter(value)
        raise AttributeError('no attribute {!r}'.format(name))

    # Safe primitive operations on _obj.

    @property
    def id(self):
        return id(self._obj)

    @property
    def typename(self):
        return get_typename(self._obj)

    @property
    def type(self):
        return type(self._obj)

    # User conveniences.

    def __repr__(self):
        return format_object(self)

    @property
    def verbose(self):
        return ReprStr(format_object(self, verbose=True))


def get_typename(obj):
    """Compute an object's type without causing side effects."""
    t = type(obj)
    m = t.__module__
    if m == '__builtin__':
        return t.__name__
    return '{}.{}'.format(m, t.__name__)


def format_summary(obj):
    """Return a string summarizing an object's type and identity."""
    otype = type(obj)
    if otype in (int, float, complex):
        return '<{} {}>'.format(otype.__name__, obj)
    elif otype in (str, unicode):
        if len(obj) > 50:
            obj = obj[:50]
            return '<{} {}+ len={}>'.format(otype.__name__, repr(obj), len(obj))
        return '<{} {}>'.format(otype.__name__, repr(obj))
    elif otype in (tuple, list, set, frozenset, dict):
        return '<{} 0x{:x} len={}>'.format(otype.__name__, id(obj), len(obj))
    return '<{} 0x{:x}>'.format(get_typename(obj), id(obj))


def iter_refs(obj):
    """Yield a (name, child) tuple for each object referenced by `obj`."""
    d = getattr(obj, '__dict__', None)
    if d is not None:
        for k, v in d.iteritems():
            yield 'a_' + k, v
    if isinstance(obj, (tuple, list)):
        for i in range(list.__len__(obj)):
            yield 'item{}'.format(i), list.__getitem__(i)
    if isinstance(obj, dict):
        for i, (k, v) in enumerate(dict.iteritems(obj)):
            yield 'key{}'.format(i), k
            yield 'value{}'.format(i), v
    elif isinstance(obj, set):
        for i, k in enumerate(set.iterkeys(obj)):
            yield 'key{}'.format(i), k


def format_object(squinter, verbose=False):
    """Render an object and its attributes as a string."""
    t = format_summary(squinter._obj)
    squinter.load()
    items = squinter.refs.items()
    items.sort()
    for name, value in items:
        t += '\n  {} {}'.format(name, format_summary(value))
    return t


class ReprStr(str):
    """A string whose repr() lacks quotation marks and escaping."""
    def __repr__(self):
        return self
