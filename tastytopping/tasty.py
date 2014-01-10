# -*- coding: utf-8 -*-

"""
.. module: api
    :platform: Unix, Windows
    :synopsis: Wrap the TastyPie API providing basic get/add/update/delete methods.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('TastyApi', )


import json
import requests

from .exceptions import (
    BadJsonResponse,
    ErrorResponse,
    NonExistantResource,
    CannotConnectToAddress,
    ResourceDeleted,
    RestMethodNotAllowed,
    IncorrectEndpointArgs,
    IncorrectEndpointKwargs,
)
from .schema import TastySchema
from . import tastytypes


class TastyApi(object):
    """Wrap the TastyPie API providing basic get/add/update/delete methods.

    :param address: URL of the TastyPie API.
    :type address: str
    """

    def __init__(self, address):
        self._addr = address
        if not address.endswith('/'):
            self._addr += '/'
        self._baseurl = None
        self._res = None
        self._sess = None
        self.auth = None

    def _session(self):
        if self._sess is None:
            self._sess = requests.session()
        return self._sess

    def _address(self):
        return self._addr

    def _resources(self):
        if self._res is None:
            self._res = self._transmit(self._session().get, self._address())
        return self._res

    def _base_url(self):
        if self._baseurl is None:
            any_endpoint = next(iter(self._resources().values()))['list_endpoint']
            excess = any_endpoint.rsplit('/', 2)[0] + '/'
            self._baseurl = self._address().replace(excess, '')
        return self._baseurl

    def _transmit(self, tx_func, url, params=None, data=None):
        if params:
            params = {k: self._encode_for_transmit(v) for k, v in params.items()}
        if data:
            data = {k: self._encode_for_transmit(v) for k, v in data.items()}
            data = json.dumps(data)
        try:
            response = tx_func(
                    url,
                    params=params,
                    data=data,
                    headers=self._headers(),
                    auth=self.auth,
            )
            response.raise_for_status()
            return response.json()
        except (ValueError, TypeError) as err:
            try:
                if response.text:
                    args = (response.text, url, params, data)
                    if 'NotFound: Invalid resource' in response.text:
                        raise NonExistantResource(*args)
                    if 'MultiValueDictKeyError: ' in response.text:
                        raise IncorrectEndpointKwargs(*args)
                    raise BadJsonResponse(*args)
            # If it was raised before the request was sent, it wasn't a JSON error.
            except UnboundLocalError:
                raise err
        except requests.exceptions.HTTPError as err:
            if response.status_code == 404 or response.status_code == 410:
                raise ResourceDeleted(url)
            raise ErrorResponse(err, response.text, url, params, data)
        except requests.exceptions.ConnectionError as err:
            raise CannotConnectToAddress(self._address())

    def _get_resource(self, resource_type):
        try:
            return self._resources()[resource_type]['list_endpoint']
        except KeyError:
            raise NonExistantResource(resource_type)

    @staticmethod
    def _encode_for_transmit(obj):
        # TODO This is getting out of control...
        if isinstance(obj, list):
            try:
                obj = [o.uri() for o in obj]
            except AttributeError:
                pass
        try:
            obj = obj.strftime(tastytypes.DATETIME_FORMAT1)
        except AttributeError:
            pass
        try:
            obj = obj.uri()
        except AttributeError:
            pass
        return obj

    @staticmethod
    def _headers():
        return {
            'accept': 'application/json',
            'content-type': 'application/json',
        }

    def _resource_url(self, resource):
        try:
            resource = resource.uri()
        except AttributeError:
            pass
        return self._base_url() + resource

    def _get_endpoint(self, base_url, method_name, *args, **kwargs):
        args_string = '/'.join(str(a) for a in args)
        url = '{0}{1}/{2}'.format(base_url, method_name, args_string)
        if not url.endswith('/'):
            url += '/'
        try:
            return self._transmit(self._session().get, url, params=kwargs)
        except NonExistantResource as err:
            raise IncorrectEndpointArgs(*err.args)

    def get(self, resource_type, schema, **kwargs):
        """Retrieve the objects for a given resource type.

        The search can be filtered by passing field=value as kwargs.

        :param resource_type: The TastyPie resource name.
        :type resource_type: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :returns: A generator object that yields dicts.
        :rtype dict
        """
        url = self._base_url() + self._get_resource(resource_type)
        schema.check_list_request_allowed('get')
        retrieve_all_results = False
        if 'limit' not in kwargs:
            retrieve_all_results = True
        result = self._transmit(self._session().get, url, params=kwargs)
        yield result
        # Only continue to retrieve results if the user hasn't specified the
        # number of results to retrieve.
        while result['meta']['next'] and retrieve_all_results:
            url = self._base_url() + result['meta']['next']
            result = self._transmit(self._session().get, url)
            yield result

    def details(self, resource, schema):
        """Retrieve the fields for a given URI.

        :param resource: A URI pointing to the TastyPie resource.
        :type resource: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :returns: The resource's fields.
        :rtype: dict
        """
        url = self._resource_url(resource)
        schema.check_detail_request_allowed('get')
        return self._transmit(self._session().get, url)

    def add(self, resource_type, schema, **kwargs):
        """Add a new resource with the given fields.

        The fields can be set by passing in field=value as kwargs.

        :param resource_type: The TastyPie resource name.
        :type resource_type: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :returns: Either the resource fields or an empty dict, depending on how
            the Resource was defined in the tastypie API (always_return_data).
        :rtype: dict
        """
        url = self._base_url() + self._get_resource(resource_type)
        schema.check_list_request_allowed('post')
        return self._transmit(self._session().post, url, data=kwargs) or {}

    def update(self, resource, schema, **kwargs):
        """Update a given resource with the given fields.

        The fields can be set by passing in field=value as kwargs.

        :param resource: A URI pointing to the TastyPie resource.
        :type resource: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :returns: Either the resource fields or an empty dict, depending on how
            the Resource was defined in the tastypie API (always_return_data).
        :rtype: dict
        """
        url = self._resource_url(resource)
        try:
            schema.check_detail_request_allowed('patch')
            method = self._session().patch
        except RestMethodNotAllowed:
            schema.check_detail_request_allowed('put')
            method = self._session().put
        return self._transmit(method, url, data=kwargs) or {}

    def delete(self, resource, schema):
        """Remove a given resource from the API.

        :param resource: A URI pointing to the TastyPie resource.
        :type resource: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        """
        url = self._resource_url(resource)
        schema.check_detail_request_allowed('delete')
        self._transmit(self._session().delete, url)

    def delete_all(self, resource_type, schema):
        """Remove the collection of resources from the API.

        :param resource_type: A URI pointing to the Tastypie resource type.
        :type resource_type: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        """
        url = self._base_url() + self._get_resource(resource_type)
        schema.check_list_request_allowed('delete')
        self._transmit(self._session().delete, url)

    def list_endpoint(self, resource_type, method_name, schema, *args, **kwargs):
        """Send a GET to a custom endpoint for this resource."""
        url = self._base_url() + self._get_resource(resource_type)
        schema.check_list_request_allowed('get')
        return self._get_endpoint(url, method_name, *args, **kwargs)

    def detail_endpoint(self, resource, method_name, schema, *args, **kwargs):
        """Send a GET to a custom endpoint for this resource instance."""
        url = self._resource_url(resource)
        schema.check_detail_request_allowed('get')
        return self._get_endpoint(url, method_name, *args, **kwargs)

    def bulk(self, resource_type, schema, resources, delete):
        """Create, update, and delete multiple resources.

        :param resource_type: The TastyPie resource name.
        :type resource_type: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :param resources: Dicts of fields to create or update.
        :type resources: list
        :param delete: URIs of resources to delete.
        :type delete: list
        """
        url = self._base_url() + self._get_resource(resource_type)
        schema.check_list_request_allowed('patch')
        data = {'objects': resources, 'deleted_objects': delete}
        # No result is returned in a 202 response.
        self._transmit(self._session().patch, url, data=data)

    def schema(self, resource_type):
        """Retrieve the schema for a given resource type.

        :param resource_type: The TastyPie resource name.
        :type resource: str
        :returns: A wrapper around the resource's schema.
        :rtype: TastySchema
        :raises: NonExistantResource
        """
        try:
            url = self._base_url() + self._resources()[resource_type]['schema']
            schema_dict = self._transmit(self._session().get, url)
            return TastySchema(schema_dict, resource_type)
        except KeyError:
            raise NonExistantResource(resource_type)
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

from .cache import retrieve_from_cache
from .api import TastyApi
from .exceptions import (
    NoResourcesExist,
    MultipleResourcesReturned,
    FieldNotInSchema,
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
            return cls.create_field_object(result, return_type)
        return _call_resource_classmethod

    @staticmethod
    def _get_resource_type(details):
        try:
            return details['resource_uri'].split('/')[-3]
        except TypeError:
            return details.split('/')[-3]

    def _create_related_resource(cls, related_details):
        resource_type = cls._get_resource_type(related_details)
        resource_class = getattr(cls._factory, resource_type)
        return resource_class(_fields=related_details)

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
            if hasattr(field, 'split'):
                return cls._create_related_resource(field)
            else:
                return [cls._create_related_resource(f) for f in field]
        elif field_type == tastytypes.DATETIME:
            # Try with milliseconds, otherwise without.
            try:
                field = datetime.strptime(field, tastytypes.DATETIME_FORMAT1)
            except ValueError:
                field = datetime.strptime(field, tastytypes.DATETIME_FORMAT2)
        return field

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
            return self._cached_field(name)
        except KeyError:
            try:
                return_type = self._schema().detail_endpoint_type(name)
            except KeyError:
                raise AttributeError(name)
            return self._resource_method(name, return_type)

    def __dir__(self):
        return sorted(set(dir(type(self)) + self.__dict__.keys() + self.fields().keys()))

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
            return self._create_field_object(result, return_type)
        return _call_resource_method

    def _create_new_resource(self, api, resource, schema, **kwargs):
        fields = self._stream_related(schema, **kwargs)
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
            field_type = schema.field(name)['type']
            if field_type == tastytypes.RELATED:
                related_type = schema.field(name)['related_type']
                if related_type == tastytypes.TO_MANY:
                    if not hasattr(value, '__iter__') and not isinstance(value[0], Resource):
                        raise BadRelatedType('Expected a list of Resources', name, value, schema.field(name))
                    fields[name] = [v.uri() for v in value]
                elif related_type == tastytypes.TO_ONE:
                    if not isinstance(value, Resource):
                        raise BadRelatedType('Expected a Resource', name, value, schema.field(name))
                    fields[name] = value.uri()
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
        # Check types for related fields and convert related types to their uris.
        fields = self._stream_related(self._schema(), **kwargs)
        # Update both the remote and local values.
        self._api().update(self.uri(), self._schema(), **fields)

    def update(self, **kwargs):
        """Set multiple fields' values at once.

        :param kwargs: The fields to update as keyword arguments.
        :type kwargs: dict
        """
        # Check that all the values passed in are allowed by the schema.
        for field, value in kwargs.items():
            self._schema().validate(field, value)
        if not self._caching:
            self._update_remote_fields(**kwargs)
        self._cached_fields.update(kwargs)

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
            self._update_remote_fields(**self._cached_fields)
        return self
