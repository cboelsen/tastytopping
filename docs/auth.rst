.. _auth:

Authentication
==============

TastyTopping supports Tastypie's authentication types, and can be set per API
and per Resource. All the authentication classes except for ``HttpApiKeyAuth``
come directly from `requests
<http://requests.readthedocs.org/en/latest/user/authentication/>`_.

For information on how authentication works in Tastypie, see their `docs
<http://django-tastypie.readthedocs.org/en/latest/authentication.html>`_.

Usage
-----

To use an authentication class in either case is very simple. As an example, to
use API key authentication for all Resources by default::

    from tastytopping import ResourceFactory, HttpApiKeyAuth
    factory = ResourceFactory('http://localhost:8000/myapp/api/v1/')
    factory.auth = HttpApiKeyAuth(username, api_key)

And to use digest authentication on a single resource (secret_resource)::

    from tastytopping import HTTPDigestAuth
    factory.secret_resource.auth = HTTPDigestAuth(username, password)

There is also a class to use with django's session authentication. This
requires that you set up a Resource in tastypie that is capable of returning
a CSRF token in a cookie, an example of which can be found in the django app
used by TastyTopping's `unit tests
<https://github.com/cboelsen/tastytopping/blob/master/tests/testsite/testapp/api.py#L50>`_.

Once a CSRF token has been returned in a cookie, telling a Resource to use
session auth is as simple as::

    from tastytopping import HTTPSessionAuth
    factory.some_resource.auth = HTTPSessionAuth()

The CSRF token will be taken from the cookies automatically. If the CSRF token
was obtained in another way, it's also possible to pass the token into
:py:class:`~tastytopping.auth.HTTPSessionAuth`'s constructor.

Besides the aforementioned auth classes, TastyTopping also provides
:py:class:`~tastytopping.auth.HTTPBasicAuth`. To use OAuth with your API,
the `requests-oathlib
<https://requests-oauthlib.readthedocs.org/en/latest/>`_ package provides a
compatible authentication class.

Do It Yourself
--------------

If it turns out that you've implemented your own authentication class on the
server-side, or you're simply using one that isn't included in TastyTopping,
then it's always possible to roll your own authentication class.

For documentation on how to do just that, see the excellent docs provided by
requests on the `subject
<http://requests.readthedocs.org/en/latest/user/advanced/#custom-authentication>`_.
For an example of how to make an authentication class that interacts with a
Tastypie Resource, see the HttpApiKeyAuth class on `github
<https://github.com/cboelsen/tastytopping/blob/master/tastytopping/auth.py>`_.
