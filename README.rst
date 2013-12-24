TastyTopping
============

Designed to take the heavy lifting out of working with django-tastypie APIs on
the client side.

Currently in beta.


Requirements
^^^^^^^^^^^^

The following needs to be installed locally to run TastyTopping:

- Python 2.7+ or Python 3.3+

- requests (`link <http://requests.readthedocs.org/en/latest/>`_) >= 1.0.0


Tested against:

- django >= 1.5.0

- django-tastypie >= 0.9.14

(see the `tox.ini
<https://github.com/cboelsen/tastytopping/blob/master/tox.ini>`_ file for
more information).


Example
^^^^^^^

A basic example, where the API looks like:

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

To use tastytopping on the client side:

::

    from datetime import datetime
    from tastytopping import ResourceFactory

    factory = ResourceFactory('http://localhost:8000/myapp/api/v1/')
    ex1 = factory.example(path='any text', rating=80)
    ex1.date = datetime.now()
    ex1_copy = factory.example.get(rating=80)
    ex1.delete()

For more information, `read the docs!
<http://tastytopping.readthedocs.org/en/latest/>`_


Justification
^^^^^^^^^^^^^

Why another one? There are some other packages around that do something similar
(most notably tastypie-queryset-client), but they're lacking in a few areas:

- Python3 support

- Support for authentication

- Development has stagnated (none of them have released in close to a year,
  whereas tastypie has been releasing thick and fast).

- I found the interfaces clunky (although that's probably personal preference).

- Making another one was FUN!
