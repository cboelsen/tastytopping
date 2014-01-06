.. _caching:

Caching
=======

By default, TastyTopping caches Resources to reduce the load on the API. This
isn't always desired though, and can (in some corner cases) even increase the
amount of traffic sent.

So, in these cases users can set the caching behaviour of Resources, and even
instances of a Resource.

Usage
-----

To turn caching off for our imaginary 'example_resource' Resource is as simple
as:

::

    from tastytopping import ResourceFactory
    factory = ResourceFactory('http://localhost:8000/myapp/api/v1/')
    factory.example_resource.caching = False

And to turn caching back on for a single instance:

::

    example1 = factory.example_resource(name='new_resource')
    example1.set_caching(True)


Behaviour
---------

Changing the caching of a Resource changes the way in which the Resource gets
and sets its data. Since a Resource a resource with caching turned on will
store its data locally, two methods are needed: One to update the local values
(:py:meth:`tastytopping.resource.Resource.refresh`),
and one to store the local values via the API
(:py:meth:`tastytopping.resource.Resource.save`).

These methods aren't needed when caching is turned off because the Resource
will retrieve its values directly from the API, and likewise will store any
values directly back via the API.

As an example, the two code segments below achieve the same result, but with
different messages passing between the Resource and the API. Firstly, the
cached resource:

::

    resource.set_caching(True)
    resource.name = 'Bob'
    resource.age = 35
    resource.save()
    resource_copy = resource.copy()
    resource_copy.birthdate = datetime(1980, 1, 1)
    resource_copy.save()
    resource.refresh()
    assert(resource_copy.birthdate == resource.birthdate)

And now the same with caching turned off:

::

    resource.set_caching(False)
    resource.name = 'Bob'
    resource.age = 35
    resource_copy = resource.copy()
    resource_copy.birthdate = datetime(1980, 1, 1)
    assert(resource_copy.birthdate == resource.birthdate)
