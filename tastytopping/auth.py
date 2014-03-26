# -*- coding: utf-8 -*-

"""
.. module: auth
    :platform: Unix, Windows
    :synopsis: A collection of auth classes to access the API.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = (
    'AuthBase',
    'HTTPApiKeyAuth',
    'HTTPSessionAuth',
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

from .exceptions import MissingCsrfTokenInCookies


class HTTPApiKeyAuth(AuthBase):
    """Use TastyPie's ApiKey authentication when communicating with the API."""

    def __init__(self, username, key):
        self._username = username
        self._key = key

    def __call__(self, req):
        req.headers['Authorization'] = 'ApiKey {0}:{1}'.format(self._username, self._key)
        return req


class HTTPSessionAuth(AuthBase):
    """Use Django's Session authentication when communicating with the API.

    The CSRF token can either be passed in on construction, or it will be
    automatically taken from the session's cookies. If no CSRF token can be
    found, a :py:class:`~tastytopping.exceptions.MissingCsrfTokenInCookies`
    exception will be raised.
    """

    def __init__(self, csrf_token=None):
        self.csrf = csrf_token

    def __call__(self, req):
        req.headers['X-CSRFToken'] = self.csrf
        return req

    def extract_csrf_token(self, cookies):
        """Get the CSRF token given a session's cookies.

        :param cookies: A session's cookies, one of which should contain the CSRF token.
        :type cookies: `CookieJar <http://docs.python.org/2/library/cookielib.html#cookielib.CookieJar>`_
        :raises: :py:class:`~tastytopping.exceptions.MissingCsrfTokenInCookies`
        """
        try:
            self.csrf = cookies['csrftoken']
        except KeyError:
            raise MissingCsrfTokenInCookies("A CSRF token isn't present in the given cookies")
