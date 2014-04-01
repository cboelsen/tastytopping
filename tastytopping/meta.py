# -*- coding: utf-8 -*-

"""
.. module: base
    :platform: Unix, Windows
    :synopsis: Class methods and behaviour for Resource.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('ResourceMeta', )


from .nested import NestedResource


class ResourceMeta(type):
    """Updates the TastyApi.auth for the class and all instances."""

    _classes = []

    def __new__(mcs, name, bases, classdict):
        try:
            auth_value = classdict.pop('auth')
        except KeyError:
            auth_value = bases[0]._auth
        # Keep track classes to update auth in property.
        obj = super(ResourceMeta, mcs).__new__(mcs, name, bases, classdict)
        mcs._classes.append(obj)
        # Move the user provided auth to a protected member.
        obj._auth = auth_value
        obj._class_api = None
        return obj

    def __len__(cls):
        return cls.all().count()

    def __getattr__(cls, name):
        if name == 'nested':
            return NestedResource(cls._full_name(), cls._api(), cls._factory)
        raise AttributeError("'{0}' class has no attribute '{1}'".format(cls, name))

    def _get_auth(cls):
        with cls._auth_lock:
            return cls._auth

    def _set_auth(cls, auth):
        with cls._auth_lock:
            def _set_api_auth(cls, auth):
                cls._auth = auth
                cls._api().auth = auth
            _set_api_auth(cls, auth)
            for derived in ResourceMeta._classes:
                if issubclass(derived, cls):
                    _set_api_auth(derived, auth)

    auth = property(_get_auth, _set_auth)
