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


from .exceptions import (
    NoResourcesExist,
    MultipleResourcesReturned,
    FieldNotInSchema,
)
from .field import create_field
from .nested import NestedResource


class ResourceMeta(type):
    """Updates the TastyApi.auth for the class and all instances."""

    _classes = []
    _alive = None
    _factory = None

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
        obj._class_resource = None
        obj._class_schema = None
        obj._full_name_ = None
        return obj

    def __len__(cls):
        return cls.count()

    def __getattr__(cls, name):
        return NestedResource(cls._full_name() + name, cls._api(), cls._factory)

    def _set_auth(cls, auth):
        def _set_api_auth(cls, auth):
            cls._auth = auth
            cls._api().auth = auth
        _set_api_auth(cls, auth)
        for derived in ResourceMeta._classes:
            if issubclass(derived, cls):
                _set_api_auth(derived, auth)

    auth = property(lambda cls: cls._auth, _set_auth)

    def filter(cls, **kwargs):
        """Return existing objects via the API, filtered by kwargs.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        exist = False
        cls._schema().check_fields_in_filters(kwargs)

        fields = {}
        for name, value in kwargs.items():
            try:
                field_type = cls._schema().field(name)['type']
                relate_name, relate_field = create_field(value, field_type, cls._factory).filter(name)
                fields[relate_name] = relate_field
            except FieldNotInSchema:
                fields[name] = value

        cls._schema().check_list_request_allowed('get')
        for response in cls._api().paginate(cls._full_name(), **fields):
            for obj in response['objects']:
                yield cls(_fields=obj)
                exist = True
        if not exist:
            raise NoResourcesExist(cls._name(), kwargs)

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
        kwargs['limit'] = 2
        resource_iter = iter(cls.filter(**kwargs))
        result = next(resource_iter)
        try:
            next(resource_iter)
            raise MultipleResourcesReturned(cls._name(), kwargs, list(resource_iter))
        except StopIteration:
            pass
        return result

    def delete_all(cls):
        """Delete the entire collection of resources.

        Besides deleting the collection of resources remotely, all local
        Resource objects of this type will be marked as deleted (ie. using any
        of them will result in a ResourceDeleted exception).
        """
        cls._schema().check_list_request_allowed('delete')
        cls._api().delete(cls._full_name())
        cls._alive = set()

    def count(cls, **kwargs):
        """Return the number of records for this resource.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: The number of records for this resource.
        :rtype: int
        """
        kwargs['limit'] = 1
        cls._schema().check_list_request_allowed('get')
        response = cls._api().get(cls._full_name(), **kwargs)
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
            resource_fields = {n: v.stream() for n, v in resource._fields().items()}
            resource_fields['resource_uri'] = resource.uri()
            resources.append(resource_fields)
        # Get the fields for any Resource objects given.
        resources = (
            [r for r in resources if not hasattr(r, 'uri')] +
            [r.fields() for r in resources if hasattr(r, 'uri')]
        )
        cls._api().bulk(
            cls._full_name(),
            cls._schema(),
            resources,
            [d.uri() for d in delete]
        )
        # Mark each deleted resource as deleted.
        for resource in delete:
            cls._alive.remove(resource.uri())

    def help(cls, verbose=False):
        """Return a string with the help for this resource's schema."""
        return cls._schema().help(verbose)
