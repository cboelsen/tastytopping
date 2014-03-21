# -*- coding: utf-8 -*-

"""
.. module: objects
    :platform: Unix, Windows
    :synopsis: Provide the magic to attach the ORM to the API.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('Resource', )


import copy


from .api import TastyApi
from .cache import retrieve_from_cache
from .exceptions import (
    ResourceDeleted,
    CreatedResourceNotFound,
    NoFiltersInSchema,
    MultipleResourcesReturned,
    FieldNotInSchema,
    ResourceHasNoUri,
    RestMethodNotAllowed,
)
from .field import create_field
from .meta import ResourceMeta
from .nested import NestedResource
from .queryset import (
    QuerySet,
    EmptyQuerySet,
)


# Required because the syntax for metaclasses changed between python 2 and 3.
# TODO Remove this when python2 finally dies.
_BASE_META_BRIDGE = ResourceMeta('_BaseMetaBridge', (object, ), {'auth': None})


class Resource(_BASE_META_BRIDGE, object):
    """A base class to inherit from, to wrap a TastyPie resource.

    To wrap a TastyPie resource, a class must be defined that inherits from
    Resource. This derived class must specify, as a minimum, the class members
    'api_url', and 'resource_name' (see below for descriptions).
    :class:`tastytopping.ResourceFactory` returns instances of this class from
    its methods. Users are strongly encouraged to use these factory methods
    instead of directly subclassing from Resource.

    :param kwargs: Keyword arguments detailing the fields for the new resource.
    :type kwargs: dict
    """

    api_url = None
    """(str): The URL to the TastyPie API (eg. http://localhost/app_name/api/v1/)."""
    resource_name = None
    """(str): The name of the resource. Defined by the 'resource_name' class
        variable in the Resource's class Meta."""
    caching = True
    """(bool): Whether to cache the resource's fields locally, or to always
        call into the API to retrieve the fields. Note that this is a class
        member variable, so updates will only apply to new objects. Use
        :meth:`tastytopping.resource.Resource.set_caching` to update an
        instance."""
    auth = None
    """(AuthBase): The Authorization to use with the resource. Note that because
        authorization applies on a per resource basis, changing the auth will
        affect all instances of a Resource, as well as the derived Resource
        class itself (TODO link to examples here)."""

    _factory = None
    _alive = set()

    def __init__(self, **kwargs):
        fields, uri = self._get_fields_and_uri_if_in_kwargs(**kwargs)
        self._set_uri(uri)
        self._set('_resource_fields', fields)
        self._set('_cached_fields', {})
        self._set('_caching', self.caching)
        self._set('_full_uri', None)
        if not self._caching and not self._uri:
            self.save()

    def __str__(self):
        return '<"{0}": {1}>'.format(self.uri(), self.fields())

    def __repr__(self):
        return '<{0} {1} @ {2}>'.format(self._name(), self.uri(), id(self))

    def __setattr__(self, name, value):
        if name not in self._fields():
            super(Resource, self).__setattr__(name, value)
        self.check_alive()
        self.update(**{name: value})

    def __getattr__(self, name):
        self.check_alive()
        try:
            return self._fields()[name].value()
        except KeyError:
            pass
        try:
            return self._schema().default(name)
        except FieldNotInSchema:
            if name == 'nested':
                return NestedResource(self.full_uri(), self._api(), self._factory)
            raise AttributeError("'{0}' object has no attribute '{1}'".format(self.__class__, name))

    def __dir__(self):
        return sorted(set(dir(type(self)) + list(self.__dict__.keys()) + list(self._fields().keys())))

    def __eq__(self, obj):
        try:
            return self.uri() == obj.uri()
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.uri())

    def __copy__(self):
        new_obj = type(self)(_fields=self.fields())
        new_obj.set_caching(self._caching)
        return new_obj

    def __deepcopy__(self, memo):
        new_obj = type(self)(_fields=copy.deepcopy(self.fields(), memo))
        new_obj.set_caching(self._caching)
        return new_obj

    def __bool__(self):
        try:
            return self.uri() in self._alive
        except ResourceHasNoUri:
            return True

    # TODO Eventually remove: This is only for python2.x compatability
    __nonzero__ = __bool__

    def _fields(self):
        if not self._resource_fields or not self._caching:
            self._schema().check_detail_request_allowed('get')
            fields = self._api().get(self.full_uri())
            fields = self._create_fields(**fields)
            self._set('_resource_fields', fields)
        return self._resource_fields

    def _set_uri(self, uri):
        if uri:
            self._alive.add(uri)
        self._set('_uri', uri)

    def _get_fields_and_uri_if_in_kwargs(self, **kwargs):
        try:
            fields = kwargs['_fields']
            if isinstance(fields, dict):
                uri = fields.get('resource_uri')
            else:
                uri = fields
                fields = {}
        except KeyError:
            uri = None
            fields = kwargs
        fields = self._create_fields(**fields)
        return fields, uri

    @classmethod
    def _create_fields(cls, **kwargs):
        fields = {}
        for name, value in kwargs.items():
            field_desc = cls._schema().field(name)
            field_type = field_desc and field_desc['type']
            fields[name] = create_field(value, field_type, cls._factory)
        return fields

    @staticmethod
    def _stream_fields(fields):
        return {n: v.stream() for n, v in fields.items()}

    def _get_this_resource(self, fields):
        fields = dict([f.filter(n) for n, f in fields.items()])
        fields = self._schema().remove_fields_not_in_filters(fields)
        fields['limit'] = 2
        self._schema().check_list_request_allowed('get')
        results = self._api().paginate(self._full_name(), **fields)
        resources = next(results)['objects']
        if len(resources) > 1:
            raise MultipleResourcesReturned(fields, resources)
        return resources[0]

    def _create_new_resource(self, **kwargs):
        fields = self._create_fields(**kwargs)
        self._schema().check_list_request_allowed('post')
        details = self._api().post(self._full_name(), **self._stream_fields(fields))
        if not details:
            try:
                details = self._get_this_resource(fields)
            except (IndexError, NoFiltersInSchema):
                raise CreatedResourceNotFound(self._name(), kwargs)
        return details

    def _update_remote_fields(self, **kwargs):
        full_uri = self.full_uri()
        fields = self._stream_fields(kwargs)
        try:
            self._schema().check_detail_request_allowed('patch')
            self._api().patch(full_uri, **fields)
        except RestMethodNotAllowed:
            self._schema().check_detail_request_allowed('put')
            current_fields = self._stream_fields(self._fields())
            current_fields.update(fields)
            self._api().put(full_uri, **current_fields)

    def _set(self, name, value):
        #Avoiding python's normal __setattr__ behaviour to avoid infinite recursion.
        attr = '_Resource{0}'.format(name) if name.startswith('__') else name
        super(Resource, self).__setattr__(attr, value)

    @classmethod
    def _api(cls):
        if cls._class_api is None:
            with cls._class_api_lock:
                if cls._class_api is None:
                    if cls.api_url is None:
                        raise NotImplementedError('"api_url" needs to be defined in a derived class.')
                    cls._class_api = retrieve_from_cache(TastyApi, cls.api_url, id=cls)
                    if cls.auth:
                        cls._class_api.auth = cls.auth
        return cls._class_api

    @classmethod
    def _schema(cls):
        if cls._class_schema is None:
            with cls._class_schema_lock:
                if cls._class_schema is None:
                    cls._class_schema = retrieve_from_cache(cls._api().schema, cls._full_name())
        return cls._class_schema

    @classmethod
    def _name(cls):
        if cls._class_resource is None:
            with cls._class_resource_lock:
                if cls._class_resource is None:
                    if cls.resource_name is None:
                        raise NotImplementedError('"resource_name" needs to be defined in a derived class.')
                    cls._class_resource = cls.resource_name
        return cls._class_resource

    @classmethod
    def _full_name(cls):
        if cls._full_name_ is None:
            with cls._full_name_lock:
                if cls._full_name_ is None:
                    cls._full_name_ = cls._api().address() + cls._name() + '/'
        return cls._full_name_

    def uri(self):
        """Return the resource_uri for this object.

        :returns: resource_uri
        :rtype: str
        """
        if self._uri is None:
            raise ResourceHasNoUri()
        return self._uri

    def full_uri(self):
        """Returns the full resource URI for this object, including server name.

        :returns: The full URI (ie. protocol + server name + resource_uri)
        :rtype: str
        """
        if self._full_uri is None:
            self._set('_full_uri', self._api().create_full_uri(self.uri()))
        return self._full_uri

    def check_alive(self):
        """Check that the Resource has not been deleted.

        Note that this only checks locally, so if another client deletes the
        resource elsewhere it won't be picked up.
        """
        if not self:
            raise ResourceDeleted(self.uri())

    def delete(self):
        """Delete the object through the API.

        Note that any attempt to use this object after calling delete will
        result in an ResourceDeleted exception.

        :raises: ResourceDeleted
        """
        self.check_alive()
        self._schema().check_detail_request_allowed('delete')
        self._api().delete(self.full_uri())
        self._alive.remove(self.uri())

    def set_caching(self, caching):
        """Set whether this object should cache its fields.

        :param caching: True to cache fields, False to always retrieve from the API.
        :type caching: bool
        """
        self._set('_caching', caching)

    def refresh(self):
        """Retrieve the latest values from the API with the next member access.

        Note that this is only useful if the Resource is caching its fields.
        """
        self._set('_resource_fields', None)
        self._set('_cached_fields', {})

    def fields(self):
        """Return the fields according to the API.

        :returns: The resource's fields as {name (str): value (object)}.
        :rtype: dict
        """
        return {n: v.value() for n, v in self._fields().items()}

    def update(self, **kwargs):
        """Set multiple fields' values at once.

        :param kwargs: The fields to update as keyword arguments.
        :type kwargs: dict
        """
        # Check that all the values passed in are allowed by the schema.
        for field, value in kwargs.items():
            self._schema().validate(field, value)
        fields = self._create_fields(**kwargs)
        if not self._caching:
            self._update_remote_fields(**fields)
        else:
            self._fields().update(fields)
            self._cached_fields.update(fields)

    def save(self):
        """Save the resource remotely, via the API.

        Note that this method only makes sense when the Resource is caching its
        fields locally (default). It is still possible to call this method when
        caching is set to False, but there won't be a noticable effect.
        """
        try:
            # Attempt to update the resource.
            self.check_alive()
            self._update_remote_fields(**self._cached_fields)
            self._set('_cached_fields', {})
        except ResourceHasNoUri:
            # No uri was found, so the resource needs to be created.
            fields = self._stream_fields(self._resource_fields)
            fields = self._create_new_resource(**fields)
            self._set_uri(fields['resource_uri'])
            fields = self._create_fields(**fields)
            self._set('_resource_fields', fields)
        return self

    def filter_field(self):
        """Return a field that can be used as a unique key for this Resource."""
        return self._schema().filterable_key()

    @classmethod
    def filter(cls, **kwargs):
        """Return existing objects via the API, filtered by kwargs.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        return QuerySet(cls, cls._schema(), cls._api(), **kwargs)

    @classmethod
    def all(cls):
        """Return all existing objects via the API.

        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        return QuerySet(cls, cls._schema(), cls._api())

    @classmethod
    def none(cls):
        """Return an EmptyQuerySet object."""
        return EmptyQuerySet(cls, cls._schema(), cls._api())

    @classmethod
    def get(cls, **kwargs):
        """Return an existing object via the API.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: The resource identified by the kwargs.
        :rtype: Resource
        :raises: NoResourcesExist, MultipleResourcesReturned
        """
        return QuerySet(cls, cls._schema(), cls._api()).get(**kwargs)

    @classmethod
    def create(cls, resources):
        """Creates new resources for each dict given.

        :param resources: A list of fields (dict) for new resources.
        :type resources: list
        """
        cls.bulk(create=resources)

    @classmethod
    def bulk(cls, create=None, update=None, delete=None):
        """Create, update, and delete to multiple resources in a single request.

        Note that this doesn't return anything, so any created resources will
        have to be retrieved with :meth:`tastytopping.resource.Resource.get` /
        :meth:`tastytopping.resource.Resource.update` /
        :meth:`tastytopping.resource.Resource.all`. Resource objects passed into
        delete will be marked as deleted, so any attempt to use them afterwards
        will raise an exception.

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
        resources = [cls._stream_fields(cls._create_fields(**res)) for res in create]
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
