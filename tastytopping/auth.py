# -*- coding: utf-8 -*-

"""
.. module: auth
    :platform: Unix, Windows
    :synopsis: A collection of auth classes to access the API.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = (
    'HttpApiKeyAuth',
    'HTTPBasicAuth',
    'HTTPDigestAuth',
)


# The unused imports are so that the classes are available from this module,
# without having to import requests.
# pylint: disable=W0611
from requests.auth import (
    AuthBase,
    HTTPBasicAuth,
    HTTPDigestAuth,
)


class HttpApiKeyAuth(AuthBase):
    """Use TastyPie's ApiKey authentication when communicating with the API."""

    def __init__(self, username, key):
        self._username = username
        self._key = key

    def __call__(self, req):
        req.headers['Authorization'] = 'ApiKey {0}:{1}'.format(self._username, self._key)
        return req
