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

from datetime import datetime

from .api import TastyApi
from .cache import retrieve_from_cache
from .exceptions import (
    NoResourcesExist,
    MultipleResourcesReturned,
    FieldNotInSchema,
)
from .fields import (
    Field,
    DateTimeField,
    ResourceField,
    ResourceListField,
)
from . import tastytypes


class ResourceMeta(type):
    """Updates the TastyApi.auth for the class and all instances."""

    _classes = []
    _alive = None
    _factory = None

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
        return cls.count()

    def __getattr__(cls, name):
        try:
            return_type = cls.schema().list_endpoint_type(name)
        except KeyError:
            raise AttributeError(name)
        def _call_resource_classmethod(*args, **kwargs):
            result = cls.api().list_endpoint(cls.resource(), name, cls.schema(), *args, **kwargs)
            return cls.create_field_object(result, return_type).value()
        return _call_resource_classmethod

    def _set_api_auth(cls, auth):
        cls._auth = auth
        cls.api().auth = auth

    def _set_auth(cls, auth):
        cls._set_api_auth(auth)
        for derived in ResourceMeta._classes:
            if issubclass(derived, cls):
                derived._set_api_auth(auth)

    auth = property(lambda cls: cls._auth, _set_auth)

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
            cls._class_api = retrieve_from_cache(TastyApi, cls.api_url, id=cls)
            if cls.auth:
                cls._class_api.auth = cls.auth
        return cls._class_api

    def schema(cls):
        """Return the schema used by this class."""
        if cls._class_schema is None:
            cls._class_schema = retrieve_from_cache(cls.api().schema, cls.resource())
        return cls._class_schema

    def create_field_object(cls, field, field_type):
        """Create an expected python object for the field_type."""
        if field is None:
            pass
        elif field_type == tastytypes.RELATED:
            if hasattr(field, 'split') or hasattr(field, 'uri'):
                return ResourceField(field, cls._factory)
            else:
                return ResourceListField(field, cls._factory)
        elif field_type == tastytypes.DATETIME:
            return DateTimeField(field)
        return Field(field)

    def get_resources(cls, **kwargs):
        """Return a generator of dicts from the API."""
        for field, obj in kwargs.items():
            try:
                if cls.schema().field(field)['type'] == tastytypes.RELATED:
                    del kwargs[field]
                    try:
                        related_field = obj.filter_field()
                        kwargs['{0}__{1}'.format(field, related_field)] = getattr(obj, related_field)
                    except AttributeError:
                        related_field = obj[0].filter_field()
                        kwargs['{0}__{1}'.format(field, related_field)] = [getattr(o, related_field) for o in obj]
            except FieldNotInSchema:
                pass
        return cls.api().get(cls.resource(), cls.schema(), **kwargs)

    def filter(cls, **kwargs):
        """Return existing objects via the API, filtered by kwargs.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        exist = False
        cls.schema().check_fields_in_filters(kwargs)
        for response in cls.get_resources(**kwargs):
            for obj in response['objects']:
                yield cls(_fields=obj)
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
        # No more than two results are needed, so save the server's resources.
        if 'limit' not in kwargs:
            kwargs['limit'] = 2
        resource_iter = iter(cls.filter(**kwargs))
        result = next(resource_iter)
        try:
            next(resource_iter)
            raise MultipleResourcesReturned(cls.resource(), kwargs, list(resource_iter))
        except StopIteration:
            pass
        return result

    def delete_all(cls):
        """Delete the entire collection of resources.

        Besides deleting the collection of resources remotely, all local
        Resource objects of this type will be marked as deleted (ie. using any
        of them will result in a ResourceDeleted exception).
        """
        cls.api().delete_all(cls.resource(), cls.schema())
        cls._alive = set()

    def count(cls, **kwargs):
        """Return the number of records for this resource.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: The number of records for this resource.
        :rtype: int
        """
        kwargs['limit'] = 1
        response = next(iter(cls.api().get(cls.resource(), cls.schema(), **kwargs)))
        return response['meta']['total_count']

    def bulk(cls, create=None, update=None, delete=None):
        """Create, update, and delete to multiple resources in a single request.

        Note that this doesn't return anything, so any created resources will
        have to be retrieved with :meth:`tastytopping.resource.Resource.get` /
        :meth:`tastytopping.resource.Resource.update` /
        :meth:`tastytopping.resource.Resource.all`, while all updated resources
        will have to be refreshed (:meth:`tastytopping.resource.Resource.refresh`).
        Resource objects passed into delete will be marked as deleted, so any
        attempt to use them afterwards will raise an exception.

        Because of the potentially large size of bulk updates, the API will
        respond with a 202 before completing the request (see `wikipedia
        <http://en.wikipedia.org/wiki/List_of_HTTP_status_codes#2xx_Success>`_,
        and `tastypie <http://django-tastypie.readthedocs.org/en/latest/interacting.html#bulk-operations>`_).
        This means it's possible for the request to fail without us knowing.
        So, while this method can be used for a sizeable optimization, there is
        a pitfall: You have been warned!

        :param create: The dicts of fields for new resources.
        :type create: list
        :param update: The Resource objects to update.
        :type update: list
        :param delete: The Resource objects to delete.
        :type delete: list
        """
        create = create or []
        update = update or []
        delete = delete or []
        for resource in update + delete:
            resource.check_alive()
        # The resources to create or update are sent in a single list.
        resources = create
        for resource in update:
            resource_fields = resource._stream_related(resource._schema(), **resource._cached_fields)
            resource_fields['resource_uri'] = resource.uri()
            resources.append(resource_fields)
        # Get the fields for any Resource objects given.
        resources = (
            [r for r in resources if not hasattr(r, 'uri')] +
            [r.fields() for r in resources if hasattr(r, 'uri')]
        )
        cls.api().bulk(
            cls.resource(),
            cls.schema(),
            resources,
            [d.uri() for d in delete]
        )
        # Mark each deleted resource as deleted.
        for resource in delete:
            cls._alive.remove(resource.uri())

    def help(cls, verbose=False):
        """Return a string with the help for this resource's schema."""
        return cls.schema().help(verbose)
