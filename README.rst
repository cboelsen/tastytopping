TastyTopping
============

.. image:: https://img.shields.io/travis/cboelsen/tastytopping/master.png
    :target: https://travis-ci.org/cboelsen/tastytopping

.. image:: https://img.shields.io/pypi/v/TastyTopping.png
    :target: https://pypi.python.org/pypi/TastyTopping


Designed to take the heavy lifting out of working with django-tastypie APIs on
the client side.


Features
^^^^^^^^

- Django model-like ORM API allowing you to GET, POST, PUT, PATCH, and DELETE::

    factory = ResourceFactory('http://localhost:8000/myapp/api/v1/')
    current_resource = factory.resource.get(field='name')    # GET
    new_resource = factory.resource(field='new_name').save() # POST
    new_resource.field = 'different_name'
    new_resource.save()                                      # PUT / PATCH
    current_resource.delete()                                # DELETE

- Easily work with any related resources::

    new_resource.children = [
        factory.resource(field='new_name1').save(),
        factory.resource(field='new_name2').save(),
    ]

- QuerySets::

    queryset1 = factory.resource.filter(field2__gt=20)
    queryset2 = queryset1.order_by('field2')
    # Evaluation happens here:
    resources = queryset2[5:-8]

- Simple way to set and update authentication per resource::

    factory.resource.auth = HTTPApiKeyAuth('username', 'key12345')

- Access nested resources using simple methods::

    new_resource.nested.nested_resource('arg1', arg2=3)

- Basic field validation before connecting to the API.

- Bulk create / update / delete to minimise API access::


    factory.resource.bulk(
        create=[{field='name1'}, {field='name2'}],
        update=[current_resource, new_resource],
        delete=[new_resource],
    )

Find more information on these features at `read the docs!
<http://tastytopping.readthedocs.org/en/latest/>`_


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


Example
^^^^^^^

A basic example of a simple workflow, using the following API on the server
side:

::

    # myapp/models.py
    # ===============
    from django.db import models

    class Example(models.Model):
        path   = models.CharField(max_length=255, unique=True)
        rating = models.IntegerField(default=50)
        date   = models.DateTimeField('date', null=True)


    # myapp/api.py
    # ============
    from .models import Example

    class ExampleResource(ModelResource):
        class Meta:
            queryset = Example.objects.all()
            resource_name = 'example'
            authorization = Authorization()
            filtering = {'path': ALL, 'rating': ALL}
            ordering = ['rating']

Using TastyTopping on the client side would look like this:

::

    from datetime import datetime
    from tastytopping import ResourceFactory

    factory = ResourceFactory('http://localhost:8000/myapp/api/v1/')
    ex1 = factory.example(path='any text', rating=80).save()
    ex1.date = datetime.now()
    ex1_copy = factory.example.get(rating=80)
    ex1.delete()

Find more examples at `read the docs!
<http://tastytopping.readthedocs.org/en/latest/>`_


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
