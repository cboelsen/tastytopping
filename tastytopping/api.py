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
    IncorrectEndpointArgs,
    IncorrectEndpointKwargs,
)
from .schema import TastySchema


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
        if data:
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

    def post(self, resource_type, schema, **kwargs):
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

    def put(self, resource, schema, **kwargs):
        """Put a given resource with the given fields.

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
        schema.check_detail_request_allowed('put')
        return self._transmit(self._session().put, url, data=kwargs) or {}

    def patch(self, resource, schema, **kwargs):
        """Patch a given resource with the given fields.

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
        schema.check_detail_request_allowed('patch')
        return self._transmit(self._session().patch, url, data=kwargs) or {}

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
