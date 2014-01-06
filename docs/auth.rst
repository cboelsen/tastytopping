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
use API key authentication for all Resources by default:

::

    from tastytopping import ResourceFactory, HttpApiKeyAuth
    factory = ResourceFactory('http://localhost:8000/myapp/api/v1/')
    factory.auth = HttpApiKeyAuth(username, api_key)

And to use digest authentication on a single resource (secret_resource):

::

    from tastytopping import HTTPDigestAuth
    factory.secret_resource.auth = HTTPDigestAuth(username, password)

Besides ``HttpApiKeyAuth`` and ``HTTPDigestAuth``, TastyTopping also provides
``HTTPBasicAuth``. To use OAuth with your API, the `requests-oathlib
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
