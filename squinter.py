"""Squinter that lets you examine live Python objects."""

import re

_unknown = object()
identifier_match = re.compile(r'[A-Za-z_][A-Za-z_0-9]*$').match

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

    def cycles(self, depth=4):
        return ReprStr(format_cycles(self._obj, depth=4))


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
    """Yield a (name, child) tuple for each object referenced by `obj`.

    In every case this routine is careful to extract references from the
    object without ever actually risking an invocation of its code.

    """
    d = getattr(obj, '__dict__', None)
    if d is not None:
        for k, v in d.iteritems():
            yield 'a_' + k, v
    if isinstance(obj, tuple):
        for i in range(tuple.__len__(obj)):
            yield 'item{}'.format(i), tuple.__getitem__(obj, i)
    if isinstance(obj, list):
        for i in range(list.__len__(obj)):
            yield 'item{}'.format(i), list.__getitem__(obj, i)
    if isinstance(obj, dict):
        for i, (k, v) in enumerate(dict.iteritems(obj)):
            tk = type(k)
            if tk is int:
                yield 'k{}'.format(k), v
            elif tk is str and identifier_match(k):
                yield 'k_' + k, v
            else:
                yield 'key{}'.format(i), k
                yield 'value{}'.format(i), v
    elif isinstance(obj, set):
        for i, k in enumerate(set.__iter__(obj)):
            yield 'member{}'.format(i), k


def format_object(squinter, verbose=False):
    """Render an object and its attributes as a string."""
    t = format_summary(squinter._obj)
    squinter.load()
    items = squinter.refs.items()
    items.sort()
    if not verbose:
        t += summarize_items(items)
    for name, value in items:
        t += '\n  {} {}'.format(name, format_summary(value))
    return t


def summarize_items(items):
    """Remove primitively-typed objects from `items` and return a summary."""
    i = 0
    counts = {int: 0, float: 0, complex: 0, str: 0, unicode: 0}
    while i < len(items):
        k, v = items[i]
        vtype = type(v)
        if vtype in counts:
            if vtype in (str, unicode):
                counts[vtype] += len(v)
            else:
                counts[vtype] += 1
            del items[i]
        else:
            i += 1
    citems = counts.items()
    citems.sort()
    return ''.join('  {}*{}'.format(k.__name__, v) for k, v in citems if v)


def format_cycles(obj, depth=4):
    """Describe the object cycles found by deliving beneath `obj`."""
    cyclelist = []
    _cycle_search(obj, (), ['_'], depth, cyclelist)
    return '\n'.join('{} <- .{}'.format(*t) for t in cyclelist)


def _cycle_search(obj, parent_ids, names, depth, cyclelist):
    parent_ids += (id(obj),)
    go_deeper = depth > 1
    for name, value in iter_refs(obj):
        names.append(name)
        if id(value) in parent_ids:
            i = parent_ids.index(id(value)) + 1
            cyclelist.append(('.'.join(names[:i]), '.'.join(names[i:])))
        elif go_deeper:
            _cycle_search(value, parent_ids, names, depth - 1, cyclelist)
        names.pop()


class ReprStr(str):
    """A string whose repr() lacks quotation marks and escaping."""
    def __repr__(self):
        return self
