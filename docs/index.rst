.. TastyTopping documentation master file, created by
   sphinx-quickstart on Wed Dec 18 15:03:05 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TastyTopping's documentation!
========================================

So, you've done all that hard work creating your REST API using `Tastypie
<http://django-tastypie.readthedocs.org/en/latest/>`_ on the server-side -
why would you want to have to do it all again on the client-side?

TastyTopping creates objects that behave similarly to django models, using your
self-documenting TastyPie REST API to create the object's attributes and
behaviour, in addition to retrieving the data. TastyTopping only needs 2 things
from you: The URL of the API, and the resource name.

As a brief example::

    >>> factory = ResourceFactory('http://localhost/app_name/api/v1')
    >>> ex = factory.example(field1='name', field2=10)
    >>> ex.field3 = datetime.now()
    >>> print ex.field4
    1.234


Contents
^^^^^^^^

.. toctree::
    :maxdepth: 1

    tutorial
    auth
    query
    nested
    optimization
    cookbook
    tastytopping


Requirements
^^^^^^^^^^^^

The following needs to be installed locally to run TastyTopping:

- Python 2.7+ or Python 3.3+

- `requests <http://requests.readthedocs.org/en/latest/>`_ >= 1.2.3


Tested with / against:

- `django <https://docs.djangoproject.com/en/1.6/>`_ >= 1.5.0

- `django-tastypie <http://django-tastypie.readthedocs.org/en/latest/>`_ >= 0.9.14

- `requests <http://requests.readthedocs.org/en/latest/>`_ >= 1.2.3

(see the `tox.ini
<https://github.com/cboelsen/tastytopping/blob/master/tox.ini>`_ file for
more information).


Justification
^^^^^^^^^^^^^

Why another one? There are some other packages around that do something
similar, but none are the complete package:

- `ORM <http://en.wikipedia.org/wiki/Object-relational_mapping>`_. A lot of
  other packages use a C-style API, which involves passing a dict with your
  data to their functions. TastyTopping wraps it all up in an ORM-style object,
  which is more OO, more elegant, and more pythonic.

- Python3 support.

- Support for authentication.

- Support for nested resources.

- QuerySets!

- A thorough set of `unit tests
  <https://github.com/cboelsen/tastytopping/blob/master/tests/tests.py>`_.

- Development has stagnated (none of them have released in close to a year,
  whereas tastypie has been releasing thick and fast).

- Creating this was FUN!


Examples
^^^^^^^^

The examples shown here relate to the following TastyPie Resources:

::

    class UserResource(ModelResource):
        class Meta:
            resource_name = 'user'
            queryset = User.objects.all()
            allowed_methods = ['get']
            authorization = Authorization()
            filtering = {
                'username': ALL,
                'id': ALL,
            }

    class ExampleResource(models.ModelResource):
        created_by = fields.ForeignKey(UserResource, 'created_by', null=True)
        class Meta:
            resource_name = 'example'
            queryset = Example.objects.all()
            list_allowed_methods   = ['get', 'post']
            detail_allowed_methods = ['get', 'post', 'put', 'delete']
            authentication = ApiKeyAuthentication()
            authorization = Authorization()
            filtering = {
                'title': ALL,
                'rating': ALL,
                'date': ALL,
                'created_by': ALL_WITH_RELATIONS,
            }
            ordering = ['rating', 'date']

The following example shows basic usage of the ORM, that will use GET, PUT,
POST, and DELETE methods on the API, using the
:py:class:`~tastytopping.ResourceFactory`

::

    from datetime import datetime
    from tastytopping import TastyFactory, HTTPApiKeyAuth

    if __name__ == "__main__":

        factory = ResourceFactory('http://example.api.com:666/test/api/v1/')
        auth = HTTPApiKeyAuth('username', '35632435657adf786c876e097f')
        factory.example.auth = auth

        new_resource = factory.example(title='A Title', rating=50)
        new_resource.date = datetime.now()
        new_resource.save()

        # Get any user from the list of users and set it to created_by:
        user = factory.user.all().first()
        new_resource.created_by = user
        # Get the new resource by its title:
        another_resource = factory.example.get(title='A Title')
        # Delete the new resource:
        new_resource.delete()
        # This will raise an exception since it's been deleted.
        print another_resource.date


Running The Tests
^^^^^^^^^^^^^^^^^

To install tastytopping:

::

    git clone https://github.com/cboelsen/tastytopping
    cd tastytopping
    virtualenv env
    . env/bin/activate  # Or, on windows, env/Scripts/activate
    pip install -U -r requirements.txt

And to run the tests:

::

    # Continued from above
    pip install tox
    tox

The tests are run against several environments with different versions of the
same packages, and are meant to pass all the tests at all times. If they aren't
passing, it's a `bug <https://github.com/cboelsen/tastytopping/issues>`_!
The tests aren't run against every combination of requests, django, and
tastypie supported, though, so there's a small chance a bug might slip in
unnoticed.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

