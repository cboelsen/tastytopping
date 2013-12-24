# -*- coding: utf-8 -*-

"""
.. module: base
    :platform: Unix, Windows
    :synopsis: Class methods and behaviour for Resource.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('ResourceMeta', )


# There's lots of protected access between base/derived/meta classes to produce
# this magic.
# pylint: disable=W0212


from . import cache
from .api import TastyApi
from .exceptions import (
    NoResourcesExist,
    MultipleResourcesReturned,
)
from .schema import TastySchema


class ResourceMeta(type):
    """Updates the TastyApi.auth for the class and all instances."""

    _classes = []

    def __new__(mcs, name, bases, classdict):
        try:
            auth_value = classdict.pop('auth')
        except KeyError:
            for base in bases:
                try:
                    auth_value = base._auth
                    break
                except AttributeError:
                    pass
        # Keep track classes to update auth in property.
        obj = super(ResourceMeta, mcs).__new__(mcs, name, bases, classdict)
        mcs._classes.append(obj)
        # Move the user provided auth to a protected member.
        obj._auth = auth_value
        obj._class_api = None
        obj._class_resource = None
        obj._class_schema = None
        return obj

    def __len__(cls):
        response = next(iter(cls.api().get(cls.resource(), cls.schema(), limit=1)))
        return response['meta']['total_count']

    def resource(cls):
        """Return the resource name of this class."""
        if cls._class_resource is None:
            if cls.resource_name is None:
                raise NotImplementedError('"resource_name" needs to be defined in a derived class.')
            cls._class_resource = cls.resource_name
        return cls._class_resource

    def api(cls):
        """Return the API used by this class."""
        if cls._class_api is None:
            if cls.api_url is None:
                raise NotImplementedError('"api_url" needs to be defined in a derived class.')
            cls._class_api = cache.get(TastyApi, cls.api_url, id=cls)
            if cls.auth:
                cls._class_api.auth = cls.auth
        return cls._class_api

    def schema(cls):
        """Return the schema used by this class."""
        if cls._class_schema is None:
            cls._class_schema = cache.get(TastySchema, cls.api(), cls.resource())
        return cls._class_schema

    def _set_api_auth(cls, auth):
        cls._auth = auth
        cls.api().auth = auth

    def _set_auth(cls, auth):
        cls._set_api_auth(auth)
        for derived in ResourceMeta._classes:
            if issubclass(derived, cls):
                derived._set_api_auth(auth)

    auth = property(lambda cls: cls._auth, _set_auth)

    def filter(cls, **kwargs):
        """Return existing objects via the API, filtered by kwargs.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        # TODO Refactor for generator
        exist = False
        for response in cls._get_details(cls.api(), cls.resource(), cls.schema(), **kwargs):
            for obj in response['objects']:
                yield cls(_details=obj)
                exist = True
        if not exist:
            raise NoResourcesExist(cls.resource(), kwargs)

    def all(cls):
        """Return all existing objects via the API.

        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        return cls.filter()

    def get(cls, **kwargs):
        """Return an existing object via the API.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: The resource identified by the kwargs.
        :rtype: Resource
        :raises: NoResourcesExist, MultipleResourcesReturned
        """
        resource_iter = iter(cls.filter(**kwargs))
        result = next(resource_iter)
        try:
            next(resource_iter)
            raise MultipleResourcesReturned(cls._derived_resource(), kwargs, list(resource_iter))
        except StopIteration:
            pass
        return result

    def count(cls):
        """Return the number of records for this resource."""
        return len(cls)
