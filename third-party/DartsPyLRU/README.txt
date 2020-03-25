
LRU Dictionaries
=================

    >>> from darts.lib.utils.lru import LRUDict

An `LRUDict` is basically a simple dictionary, which has a defined
maximum capacity, that may be supplied at construction time, or modified
at run-time via the `capacity` property::

    >>> cache = LRUDict(1)
    >>> cache.capacity
    1

The minimum capacity value is 1, and LRU dicts will complain, if someone
attempts to use a value smaller than that::

    >>> cache.capacity = -1                              #doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: -1 is not a valid capacity
    >>> LRUDict(-1)                                      #doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: -1 is not a valid capacity

LRU dictionaries can never contain more elements than their capacity value
indicates, so::

    >>> cache[1] = "First"
    >>> cache[2] = "Second"
    >>> len(cache)
    1

In order to ensure this behaviour, the dictionary will evict entries if
it needs to make room for new ones. So::

    >>> 1 in cache
    False
    >>> 2 in cache
    True

The capacity can be adjusted at run-time. Growing the capacity does not
affect the number of elements present in an LRU dictionary::

    >>> cache.capacity = 3
    >>> len(cache)
    1
    >>> cache[1] = "First"
    >>> cache[3] = "Third"
    >>> len(cache)
    3

but shrinking does::

    >>> cache.capacity = 2
    >>> len(cache)
    2
    >>> sorted(list(cache.iterkeys()))
    [1, 3]

Note, that the entry with key `2` was evicted, because it was the oldest
entry at the time of the modification of `capacity`. The new oldest entry
is the one with key `1`, which can be seen, when we try to add another
entry to the dict::

    >>> cache[4] = "Fourth"
    >>> sorted(list(cache.iterkeys()))
    [3, 4]

The following operations affect an entry's priority::

- `get`
- `__getitem__`
- `__setitem__`
- `__contains__`

Calling any of these operations on an existing key will boost the key's
priority, making it more unlikely to get evicted, when the dictionary needs
to make room for new entries. There is a special `peek` operation, which
returns the current value associated to a key without boosting the priority
of the entry::

    >>> cache.peek(3)
    'Third'
    >>> cache[5] = "Fifth"
    >>> sorted(list(cache.iterkeys()))
    [4, 5]

As you can see, even though we accessed the entry with key `3` as the last
one, the entry is now gone, because it did not get a priority boost from 
the call to `peek`.

The class `LRUDict` supports a subset of the standard Python `dict` 
interface. In particular, we can iterate over the key, values, and 
items of an LRU dict::

    >>> sorted([k for k in cache.iterkeys()])
    [4, 5]
    >>> sorted([v for v in cache.itervalues()])
    ['Fifth', 'Fourth']
    >>> sorted([p for p in cache.iteritems()])
    [(4, 'Fourth'), (5, 'Fifth')]
    >>> sorted(list(cache))
    [4, 5]

Note, that there is no guaranteed order; in particular, the elements are 
not generated in priority order or somesuch. Similar to regular `dict`s,
an LRU dict's `__iter__` is actually any alias for `iterkeys`.

Furthermore, we can remove all elements from the dict:

    >>> cache.clear()
    >>> sorted(list(cache.iterkeys()))
    []


Thread-safety
--------------

Instances of class `LRUDict` are not thread safe. Worse: even concurrent
read-only access is not thread-safe and has to be synchronized by the
client application.

There is, however, the class `SynchronizedLRUDict`, which exposes the
same interface as plain `LRUDict`, but fully thread-safe. The following 
session contains exactly the steps, we already tried with a plain `LRUDict`, 
but now using the synchronized version::

    >>> from darts.lib.utils.lru import SynchronizedLRUDict
    >>> cache = SynchronizedLRUDict(1)
    >>> cache.capacity
    1
    >>> cache.capacity = -1                              #doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: -1 is not a valid capacity
    >>> LRUDict(-1)                                      #doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: -1 is not a valid capacity
    >>> cache[1] = "First"
    >>> cache[2] = "Second"
    >>> len(cache)
    1
    >>> 1 in cache
    False
    >>> 2 in cache
    True
    >>> cache.capacity = 3
    >>> len(cache)
    1
    >>> cache[1] = "First"
    >>> cache[3] = "Third"
    >>> len(cache)
    3
    >>> cache.capacity = 2
    >>> len(cache)
    2
    >>> sorted(list(cache.iterkeys()))
    [1, 3]
    >>> cache[4] = "Fourth"
    >>> sorted(list(cache.iterkeys()))
    [3, 4]
    >>> cache.peek(3)
    'Third'
    >>> cache[5] = "Fifth"
    >>> sorted(list(cache.iterkeys()))
    [4, 5]
    >>> sorted([k for k in cache.iterkeys()])
    [4, 5]
    >>> sorted([v for v in cache.itervalues()])
    ['Fifth', 'Fourth']
    >>> sorted([p for p in cache.iteritems()])
    [(4, 'Fourth'), (5, 'Fifth')]
    >>> sorted(list(cache))
    [4, 5]
    >>> cache.clear()
    >>> sorted(list(cache.iterkeys()))
    []


Auto-loading Caches
====================

Having some kind of dictionary which is capable of cleaning itself
up is nice, but in order to implement caching, there is still something
missing: the mechanism, which actually loads something into our dict.
This part of the story is implemented by the `AutoLRUCache`::

    >>> from darts.lib.utils.lru import AutoLRUCache

Let's first define a load function::

    >>> def load_resource(key):
    ...    if key < 10:
    ...        print "Loading %r" % (key,)
    ...        return "R(%s)" % (key,)

and a cache::

    >>> cache = AutoLRUCache(load_resource, capacity=3)
    >>> cache.load(1)
    Loading 1
    'R(1)'
    >>> cache.load(1)
    'R(1)'

As you can see, the first time, an actual element is loaded, the load
function provided to the constructor is called, in order to provide the
actual resource value. On subsequent calls to `load`, the cached value
is returned.

Internally, the `AutoLRUCache` class uses an `LRUDict` to cache values,
so::

    >>> cache.load(2)
    Loading 2
    'R(2)'
    >>> cache.load(3)
    Loading 3
    'R(3)'
    >>> cache.load(4)
    Loading 4
    'R(4)'
    >>> cache.load(1)
    Loading 1
    'R(1)'

Note the "Loading 1" line in the last example. The cache has been initialized
with a capacity of 3, so the value of key `1` had to be evicted when the one
for key `4` was loaded. When we tried to obtain `1` again, the cache had to
properly reload it, calling the loader function.

If there is actually no resource for a given key value, the loader function
must return `None`. It follows, that `None` is never a valid resource value
to be associated with some key in an `AutoLRUCache`.

    >>> cache.load(11, 'Oops')
    'Oops'


Thread-safety
--------------

Instances of class `AutoLRUCache` are fully thread safe. Be warned, though,
that the loader function is called outside of any synchronization scope the
class may internally use, and has to provide its own synchronization if 
required.

The cache class actually tries to minimize the number of invocations of the
loader by making sure, that no two concurrent threads will try to load the
same key value (though any number of concurrent threads might be busy loading
the resources associated with different keys).


Caching and stale entries
==========================

There is another `AutoLRUCache`-like class provided by the LRU module,
which gives more control over timing out of entries than `AutoLRUCache` does.


    >>> from darts.lib.utils.lru import DecayingLRUCache
    >>> current_time = 0
    >>> def tick():
    ...     global current_time
    ...     current_time += 1

Here, we defined a simple "clock". We could have used the system clock,
but roling our own here gives us more control over the notion of "time".
Now, let's define a simple cache entry:

    >>> from collections import namedtuple
    >>> Entry = namedtuple("Entry", "timestamp payload")
    >>> def make_entry(payload):
    ...     return Entry(current_time, payload)

and a loader function

    >>> def load(full_key):
    ...     print "Loading", full_key
    ...     return make_entry(u"Entry for %r" % (full_key,))

For the following parts, we consider an entry to be "too old", if it has
been created more then two "ticks" ago:

    >>> def is_still_current(entry):
    ...    return current_time - entry.timestamp <= 2

Finally, we create another cache thingy

    >>> cache = DecayingLRUCache(load, tester=is_still_current, capacity=3)

The `DecayingLRUCache` shows much of the same behaviour of the `AutoLRUCache`,
namely:

    >>> cache.load(1)
    Loading 1
    Entry(timestamp=0, payload=u'Entry for 1')
    >>> cache.load(2)
    Loading 2
    Entry(timestamp=0, payload=u'Entry for 2')
    >>> cache.load(3)
    Loading 3
    Entry(timestamp=0, payload=u'Entry for 3')
    >>> cache.load(4)
    Loading 4
    Entry(timestamp=0, payload=u'Entry for 4')
    >>> cache.load(1)
    Loading 1
    Entry(timestamp=0, payload=u'Entry for 1')
    
The entry with key `1` had to be reloaded, since the cache has a capacity of
3, and the old entry for `1` was evicted when the entry for `4` was loaded
and we needed to make room.

    >>> cache.load(3)
    Entry(timestamp=0, payload=u'Entry for 3')

Now, let's advance time

    >>> tick()
    >>> cache.load(3)
    Entry(timestamp=0, payload=u'Entry for 3')

The entry is still available. 

    >>> tick()
    >>> cache.load(3)
    Entry(timestamp=0, payload=u'Entry for 3')
    >>> tick()
    >>> cache.load(3)
    Loading 3
    Entry(timestamp=3, payload=u'Entry for 3')

Note, that eviction is still based on LRU, not on the age test. 


Change Log
==========

Version 0.5
------------

Added a "from __future__ import with_statement" for Python 2.5 compatibility.
Note, that supporting py2.5 is not a real goal, and I did not test the code
using that version.

Version 0.4
------------

Added class `DecayingLRUCache` 

Version 0.3
------------

Added class `SynchronizedLRUDict` as thread-safe counterpart for `LRUDict`.

