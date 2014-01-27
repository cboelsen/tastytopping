# -*- coding: utf-8 -*-

"""
.. module: objects
    :platform: Unix, Windows
    :synopsis: Provide the magic to attach the ORM to the API.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('Resource', )


from .meta import ResourceMeta
from .exceptions import (
    ResourceDeleted,
    CreatedResourceNotFound,
    NoFiltersInSchema,
    BadRelatedType,
    MultipleResourcesReturned,
)
from .field import create_field
from . import tastytypes


# Required because the syntax for metaclasses changed between python 2 and 3.
# TODO Remove this when python2 finally dies.
_BaseMetaBridge = ResourceMeta('_BaseMetaBridge', (object, ), {'auth': None})  # This is a class, not a constant # pylint: disable=C0103


class Resource(_BaseMetaBridge, object):
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

    _alive = set()

    def __init__(self, **kwargs):
        fields, uri = self._get_fields_and_uri_if_in_kwargs(**kwargs)
        self._set_uri(uri)
        self._set('_init_kwargs', kwargs)
        self._set('_fields', fields)
        self._set('_cached_fields', {})
        self._set('_caching', self.caching)
        self._set('filter_field', self._schema().filterable_key)

    def __str__(self):
        return '<"{0}": {1}>'.format(self.uri(), self.fields())

    def __repr__(self):
        return '<{0} {1} @ {2}>'.format(self._resource(), self.uri(), id(self))

    def __setattr__(self, name, value):
        if name not in self.fields():
            super(Resource, self).__setattr__(name, value)
        self.check_alive()
        self.update(**{name: value})

    def __getattr__(self, name):
        self.check_alive()
        try:
            return self._cached_field(name).value()
        except KeyError:
            try:
                return_type = self._schema().detail_endpoint_type(name)
            except KeyError:
                raise AttributeError(name)
            return self._resource_method(name, return_type)

    def __dir__(self):
        return sorted(set(dir(type(self)) + list(self.__dict__.keys()) + list(self.fields().keys())))

    def __eq__(self, obj):
        try:
            return self.uri() == obj.uri()
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.uri())

    def __bool__(self):
        return self.uri() in self._alive

    # TODO Eventually remove: This is only for python2.x compatability
    __nonzero__ = __bool__

    def _set_uri(self, uri):
        if uri:
            self._alive.add(uri)
        self._set('_uri', uri)

    def _get_fields_and_uri_if_in_kwargs(self, **kwargs):
        try:
            fields = kwargs['_fields']
            if isinstance(fields, dict):
                uri = fields['resource_uri']
                kwargs = {'_fields': fields['resource_uri']}
            else:
                uri = fields
                fields = None
        except KeyError:
            uri = None
            fields = None
        return fields, uri

    def _resource_method(self, method_name, return_type):
        def _call_resource_method(*args, **kwargs):
            result = self._api().detail_endpoint(self, method_name, self._schema(), *args, **kwargs)
            return self._create_field_object(result, return_type).value()
        return _call_resource_method

    def _create_new_resource(self, api, resource, schema, **kwargs):
        fields = {}
        for name, value in kwargs.items():
            field_type = self._schema().field(name)['type']
            fields[name] = self._create_field_object(value, field_type)
        fields = {n: v.stream() for n, v in fields.items()}
        details = api.add(resource, schema, **fields)
        if not details:
            try:
                kwargs['limit'] = 2
                fields = schema.remove_fields_not_in_filters(kwargs)
                results = type(self).get_resources(**fields)
                resources = next(iter(results))['objects']
                if len(resources) > 1:
                    raise MultipleResourcesReturned(fields, resources)
                details = resources[0]
            except (IndexError, NoFiltersInSchema):
                raise CreatedResourceNotFound(resource, schema, kwargs)
        return details

    @staticmethod
    def _stream_related(schema, **kwargs):
        fields = kwargs.copy()
        for name, value in fields.items():
            # TODO Get rid!
            try:
                value = value.value()
            except AttributeError:
                pass
            field_type = schema.field(name)['type']
            if field_type == tastytypes.RELATED:
                related_type = schema.field(name)['related_type']
                if related_type == tastytypes.TO_MANY:
                    try:
                        fields[name] = [v.uri() for v in value]
                    except (TypeError, AttributeError):
                        raise BadRelatedType('Expected a list of Resources', name, value, schema.field(name))
                elif related_type == tastytypes.TO_ONE:
                    try:
                        fields[name] = value.uri()
                    except AttributeError:
                        raise BadRelatedType('Expected a Resource', name, value, schema.field(name))
        return fields

    def _cached_field(self, name):
        if name not in self._cached_fields or not self._caching:
            field = self.fields()[name]
            field_type = self._schema().field(name)['type']
            self._cached_fields[name] = self._create_field_object(field, field_type)
        return self._cached_fields[name]

    def _set(self, name, value):
        #Avoiding python's normal __setattr__ behaviour to avoid infinite recursion.
        attr = '_Resource{0}'.format(name) if name.startswith('__') else name
        super(Resource, self).__setattr__(attr, value)

    _api = classmethod(lambda cls: cls.api())
    _resource = classmethod(lambda cls: cls.resource())
    _schema = classmethod(lambda cls: cls.schema())
    _create_field_object = classmethod(lambda cls, field, field_type: cls.create_field_object(field, field_type))

    def uri(self):
        """Return the resource_uri for this object.

        :returns: resource_uri
        :rtype: str
        """
        if self._uri is None:
            self._set_uri(self.fields()['resource_uri'])
        return self._uri

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
        self._api().delete(self.uri(), self._schema())
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
        self._set('_fields', None)
        self._set('_cached_fields', {})

    def fields(self):
        """Return the fields according to the API.

        :returns: The resource's fields.
        :rtype: list
        """
        if self._fields is None or not self._caching:
            if self._uri:
                fields = self._api().details(self._uri, self._schema())
            else:
                # TODO This is a new Resource - the fields should be written on
                # a save(), not an access!
                fields = self._create_new_resource(self._api(), self._resource(), self._schema(), **self._init_kwargs)
                self._set_uri(fields['resource_uri'])
            self._set('_init_kwargs', {})
            self._set('_fields', fields)
        return self._fields

    def _update_remote_fields(self, **kwargs):
        # Update both the remote and local values.
        self._api().update(self.uri(), self._schema(), **kwargs)

    def update(self, **kwargs):
        """Set multiple fields' values at once.

        :param kwargs: The fields to update as keyword arguments.
        :type kwargs: dict
        """
        # Check that all the values passed in are allowed by the schema.
        for field, value in kwargs.items():
            self._schema().validate(field, value)
        if not self._caching:
            fields = {}
            for name, value in kwargs.items():
                field_type = self._schema().field(name)['type']
                fields[name] = self._create_field_object(value, field_type)
            fields = {n: v.stream() for n, v in fields.items()}
            self._update_remote_fields(**fields)
        for name, value in kwargs.items():
            field_type = self._schema().field(name)['type']
            self._cached_fields[name] = self._create_field_object(value, field_type)

    def save(self):
        """Save the resource remotely, via the API.

        Note that this method only makes sense when the Resource is caching its
        fields locally (default). It is still possible to call this method when
        caching is set to False, but there won't be a noticable effect.
        """
        self.check_alive()
        # TODO Remove reference to fields() when new resource creation moves
        # to here!
        self.fields()
        if self._cached_fields:
            fields = {n: v.stream() for n, v in self._cached_fields.items()}
            self._update_remote_fields(**fields)
        return self
