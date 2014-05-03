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
    ErrorResponse,
    CannotConnectToAddress,
    ResourceDeleted,
    IncorrectNestedResourceKwargs,
    BadUri,
    RestMethodNotAllowed,
)
from .lock import PickleLock
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
        self._sess = None
        self._sess_lock = PickleLock()
        self._auth = None
        self._auth_lock = PickleLock()
        self.verify = True

    def _session(self):
        if self._sess is None:
            with self._sess_lock:
                if self._sess is None:
                    self._sess = requests.session()
        return self._sess

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
                verify=self.verify,
            )
            response.raise_for_status()
            return response.json()
        except (ValueError, TypeError) as err:
            try:
                if response.text:
                    args = (response.text, err, url, params, data)
                    if 'NotFound: Invalid resource' in response.text:
                        raise AttributeError(*args)
                    if 'KeyError: ' in response.text:
                        raise IncorrectNestedResourceKwargs(*args)
                    raise ErrorResponse(*args)
            # If it was raised before the request was sent, it wasn't a JSON error.
            except UnboundLocalError:
                raise err
        except requests.exceptions.HTTPError as err:
            if response.status_code == 404 or response.status_code == 410:
                raise ResourceDeleted(url)
            if response.status_code == 405:
                raise RestMethodNotAllowed(err, url, tx_func)
            raise ErrorResponse(response.text, err, url, params, data)
        except requests.exceptions.ConnectionError as err:
            raise CannotConnectToAddress(self.address())

    @staticmethod
    def _headers():
        return {
            'accept': 'application/json',
            'content-type': 'application/json',
        }

    def _set_auth(self, auth):
        with self._auth_lock:
            try:
                current_csrf = auth.csrf
            except AttributeError:
                pass
            else:
                if current_csrf is None:
                    auth.extract_csrf_token(self._session().cookies)
            self._auth = auth

    def _get_auth(self):
        with self._auth_lock:
            return self._auth

    auth = property(_get_auth, _set_auth)

    def address(self):
        """Return the address of the API."""
        return self._addr

    def create_full_uri(self, uri):
        """Return the full address of the given URI."""
        uri_cutoff = len(uri)
        while uri_cutoff > 2:
            uri_cutoff -= 1
            if self.address().endswith(uri[:uri_cutoff]):
                return self.address() + uri[uri_cutoff:]
        raise BadUri(u'Could not find full uri. Address = "{0}", URI = "{1}"'.format(self.address(), uri))

    def paginate(self, url, **kwargs):
        """Retrieve the objects for a given resource type.

        The search can be filtered by passing field=value as kwargs.

        :param url: The URL of the TastyPie resource.
        :type url: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :returns: A generator object that yields dicts.
        :rtype: dict
        """
        limit = kwargs.get('limit', 0) or 1000000000    # Stupidly large number to simulate 'unlimited'.
        result = self._transmit(self._session().get, url, params=kwargs)
        limit -= int(result['meta']['limit'])
        yield result
        while result['meta']['next'] and limit > 0:
            url = self.create_full_uri(result['meta']['next'])
            result = self._transmit(self._session().get, url, params={'limit': limit})
            limit -= int(result['meta']['limit'])
            yield result

    def get(self, url, **kwargs):
        """Retrieve the fields for a given URI.

        :param url: The URL of the TastyPie resource.
        :type resource: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :returns: The resource's fields.
        :rtype: dict
        """
        return self._transmit(self._session().get, url, params=kwargs)

    def post(self, url, **kwargs):
        """Add a new resource with the given fields.

        The fields can be set by passing in field=value as kwargs.

        :param url: The URL of the TastyPie resource.
        :type resource_type: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :returns: Either the resource fields or an empty dict, depending on how
            the Resource was defined in the tastypie API (always_return_data).
        :rtype: dict
        """
        return self._transmit(self._session().post, url, data=kwargs) or {}

    def put(self, url, **kwargs):
        """Put a given resource with the given fields.

        The fields can be set by passing in field=value as kwargs.

        :param url: The URL of the TastyPie resource.
        :type resource: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :returns: Either the resource fields or an empty dict, depending on how
            the Resource was defined in the tastypie API (always_return_data).
        :rtype: dict
        """
        return self._transmit(self._session().put, url, data=kwargs) or {}

    def patch(self, url, **kwargs):
        """Patch a given resource with the given fields.

        The fields can be set by passing in field=value as kwargs.

        :param url: The URL of the TastyPie resource.
        :type resource: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :returns: Either the resource fields or an empty dict, depending on how
            the Resource was defined in the tastypie API (always_return_data).
        :rtype: dict
        """
        return self._transmit(self._session().patch, url, data=kwargs) or {}

    def delete(self, url):
        """Remove a given resource from the API.

        :param url: The URL of the TastyPie resource.
        :type resource: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        """
        self._transmit(self._session().delete, url)

    def bulk(self, url, schema, resources, delete):
        """Create, update, and delete multiple resources.

        :param url: The URL of the TastyPie resource.
        :type resource_type: str
        :param schema: The schema to use for validation.
        :type schema: TastySchema
        :param resources: Dicts of fields to create or update.
        :type resources: list
        :param delete: URIs of resources to delete.
        :type delete: list
        """
        schema.check_list_request_allowed('patch')
        data = {'objects': resources, 'deleted_objects': delete}
        # No result is returned in a 202 response.
        self._transmit(self._session().patch, url, data=data)

    def schema(self, url):
        """Retrieve the schema for a given resource type.

        :param url: The URL of the TastyPie resource.
        :type resource: str
        :returns: A wrapper around the resource's schema.
        :rtype: TastySchema
        """
        url += 'schema/'
        schema_dict = self._transmit(self._session().get, url)
        return TastySchema(schema_dict, url)

    def resources(self):
        """Return the resources available from this API.

        :returns: A list of available resources as strings.
        :rtype: list
        :raises: CannotConnectToAddress
        """
        return self._transmit(self._session().get, self.address()).keys()
