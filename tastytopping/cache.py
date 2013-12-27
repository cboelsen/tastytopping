# -*- coding: utf-8 -*-

"""
.. module: cache
    :platform: Unix, Windows
    :synopsis: Cache living objects here to prevent needless creation.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('retrieve_from_cache', )


import weakref


_STORAGE = weakref.WeakValueDictionary()


def retrieve_from_cache(class_type, *args, **kwargs):
    """Access the cache and return the desired object.

    If the object doesn't exist in the cache, a new object will be created
    using the args and kwargs given. Note that this module uses weakrefs, so if
    the object no longer exists outside of the cache, it will be destroyed
    (ie. a proper singleton).

    :param class_type: The type of object to retrieve.
    :type class_type: A class (any callable object returning another object).
    :param id: optional keyword argument to further identify the cached object
        to retrieve.
    :rtype id: object
    :returns: Either the cached object, or a brand new object.
    :rtype: class_type (given by the user).
    """
    stored_id = args + (class_type, )
    if 'id' in kwargs:
        stored_id += (kwargs.pop('id'), )
    try:
        factory_object = _STORAGE[stored_id]
    except KeyError:
        factory_object = class_type(*args, **kwargs)
        _STORAGE[stored_id] = factory_object
    return factory_object
