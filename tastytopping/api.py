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
)
from .schema import TastySchema
from . import tastytypes


class TastyApi(object):
    """Wrap the TastyPie API providing basic get/add/update/delete methods.

    :var max_results: initial value: 100
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
        self.max_results = 100

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
                    raise BadJsonResponse(err, response.text, url, params, data)
            # If it was raised before the request was sent, it wasn't a JSON error.
            except UnboundLocalError:
                raise err
        except requests.exceptions.HTTPError as err:
            if response.status_code == 404:
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
            kwargs.update({'limit': self.max_results})
            retrieve_all_results = True
        result = self._transmit(self._session().get, url, params=kwargs)
        yield result
        # Only continue to retrieve results if the user hasn't specified the
        # number of results to retrieve.
        while result['meta']['next'] and retrieve_all_results:
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
