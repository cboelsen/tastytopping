TastyTopping
============

Designed to take the heavy lifting out of working with django-tastypie APIs on
the client side.

Currently in beta.


Features
^^^^^^^^

- Django model-like ORM API allowing you to GET, POST, PUT, PATCH, and DELETE:

  ::

      factory = ResourceFactory('http://localhost:8000/myapp/api/v1/')
      current_resource = factory.resource.get(field='name')    # GET
      new_resource = factory.resource(field='new_name').save() # POST
      new_resource.field = 'different_name'                    # PATCH / PUT
      current_resource.delete()                                # DELETE

- Easily work with any related resources:

  ::

      new_resource.children = [
          factory.resource(field='new_name1').save(),
          factory.resource(field='new_name2').save(),
      ]

- Simple way to set and update authentication per resource:

  ::

      factory.resource.auth = ApiKeyAuth('username', 'key12345')

- Access nested resources using simple methods (currently in dev branch):

  ::

      new_resource.nested_resource('arg1', arg2=3)

- Set whether the resources should be cached locally or always updated remotely
  (per resource or per instance):

  ::

      factory.resource.caching = False
      # Or per instance
      new_resource.set_caching(False)

- Basic field validation before connecting to the API.

- Bulk create / update / delete to minimise API access:

  ::

      factory.resource.bulk(
          create=[{field='name1'}, {field='name2'}],
          update=[current_resource, new_resource],
          delete=[new_resource],
      )

- Auto-generate docs for your tastypie API (in progress).

Find more information on these features at `read the docs!
<http://tastytopping.readthedocs.org/en/latest/>`_


Requirements
^^^^^^^^^^^^

The following needs to be installed locally to run TastyTopping:

- Python 2.7+ or Python 3.3+

- `requests <http://requests.readthedocs.org/en/latest/>`_ >= 1.0.0


Tested with / against:

- `django <https://docs.djangoproject.com/en/1.6/>`_ >= 1.5.0

- `django-tastypie <http://django-tastypie.readthedocs.org/en/latest/>`_ >= 0.9.14

- `requests <http://requests.readthedocs.org/en/latest/>`_ >= 1.0.0

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
similar, but they're lacking in a few areas:

- `ORM <http://en.wikipedia.org/wiki/Object-relational_mapping>`_. A lot of
  other packages need both the resource data and the API wrapper to work with
  a resource, instead of just a resource-type object (which is more pythonic).

- Python3 support.

- Support for authentication.

- Support for nested resources.

- A thorough set of `unit tests
  <https://github.com/cboelsen/tastytopping/blob/master/tests/tests.py>`_.

- Development has stagnated (none of them have released in close to a year,
  whereas tastypie has been releasing thick and fast).

- Creating this was FUN!
