# -*- coding: utf-8 -*-

"""
.. module: api
    :platform: Unix, Windows
    :synopsis: Wrap the TastyPie API providing basic get/add/update/delete methods.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('Api', )


import json
import requests

# TODO Be exact!
from .exceptions import *


class Api(object):

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
                    raise BadJsonResponse(*args)
            # If it was raised before the request was sent, it wasn't a JSON error.
            except UnboundLocalError:
                raise err
        except requests.exceptions.HTTPError as err:
            if response.status_code == 404 or response.status_code == 410:
                raise ResourceDeleted(url)
            raise ErrorResponse(err, response.text, url, params, data)
        except requests.exceptions.ConnectionError as err:
            raise CannotConnectToAddress(self.address())

    @staticmethod
    def _headers():
        return {
            'accept': 'application/json',
            'content-type': 'application/json',
        }

    def address(self):
        return self._addr

    def get(self, url, **kwargs):
        return self._transmit(self._session().get, url, params=kwargs)

    def post(self, url, **kwargs):
        return self._transmit(self._session().post, url, data=kwargs) or {}

    def put(self, url, **kwargs):
        return self._transmit(self._session().put, url, data=kwargs) or {}

    def patch(self, resource, **kwargs):
        return self._transmit(self._session().patch, url, data=kwargs) or {}

    def delete(self, url):
        self._transmit(self._session().delete, url)
