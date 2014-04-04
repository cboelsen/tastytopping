.. _nested:

Nested Resources
================

Nested resources allow you to extend the functionality of a tastypie Resource
in a nice and simple way. It would make sense to access that nested resource on
the client-side in a nice and simple way too, which is exactly what
TastyTopping does. For information on how to create nested resources in
tastypie, check out `tastypie's docs
<http://django-tastypie.readthedocs.org/en/latest/cookbook.html#nested-resources>`_
and TastyTopping's `unit test webapp
<https://github.com/cboelsen/tastytopping/blob/master/tests/testsite/testapp/api.py>`_.

Usage
-----

A Resource's nested resources are accessible via the 'nested' attribute. Any
attribute that accessed from 'nested' will be assumed to be a nested resource,
since there's no standard way of accessing that information via a schema.

The examples below will illustrate what's configured on the server side by
showing the contents of a Resource's ``prepend_urls()`` method. Nested
resources can be appended to both the list view and detail view, so we'll
go through a couple of examples of each.

List View
^^^^^^^^^

::

    # api.py on the server-side
    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>{0})/add/(?P<num1>\d+)/(?P<num2>\d+){1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('calc_add'),
                name="api_calc_add",
            ),
        ]

So, in this (silly) example, we've got a nested resource at
``<resource_name>/add/<num1>/<num2>/``, which we'll access with a GET::

    # client-side
    factory = ResourceFactory('http://some-server.com/api/v1/')
    my_sum = factory.some_resource.nested.add(2, 3).get()

This will send a GET request to ``/api/v1/some_resource/add/2/3/``. A
NestedResource will accept any ``*args`` and just append them to the URL. So::

    factory.some_resource.nested.add(2, 3, 4, 5).get()

will send a GET request to ``/api/v1/some_resource/add/2/3/4/5/``. In this case
there's no matching URL on the server side, and you'll get an exception.

It's also possible to send POST, PUT, PATCH, and DELETE requests. In these
instances it makes more sense to send any extra information as data::

    # api.py on the server-side
    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>{0})/mult{1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('calc_mult'),
                name="api_calc_mult",
            ),
        ]

What you can't see here is that ``calc_mult()`` accepts only POST requests, and
expects two numbers as part of a dict (for example ``{num1: 1, num2: 2}``) in
the request's data. With that in mind, sending a request to this nested
resource using TastyTopping looks like::

    # client-side
    factory = ResourceFactory('http://some-server.com/api/v1/')
    my_product = factory.some_resource.nested.mult(num1=2, num2=3).post()

This will send a POST request to ``/api/v1/some_resource/mult/``, and include
the kwargs as the data dictionary.

Detail View
^^^^^^^^^^^

Now we'll take a look at a nested resource as part of a Resource's detail view.
On tastypie's side, the matching regex will include the ``pk``, which will be
passed to the called method::

    # api.py on the server-side
    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>{0})/(?P<pk>\w[\w/-]*)/chained/getting/child{1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_child'),
                name="api_get_child",
            ),
        ]

``get_child()`` expects no arguments, and will return a resource. To send a GET
request to this nested resource is as simple as::

    # client-side
    factory = ResourceFactory('http://some-server.com/api/v1/')
    a_resource = factory.some_resource.all().first()
    child = a_resource.nested.chained.getting.child.get()
    # Or, if you find it more readable:
    child = a_resource.nested.chained.getting('child').get()
