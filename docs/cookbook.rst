.. _cookbook:

TastyTopping Cookbook
=====================

Extending Resources
-------------------

Since the :py:class:`~tastytopping.ResourceFactory` returns classes
for a resource's list view, it's possible to inherit from these to extend their
functionality. For instance, if you want each Resource to keep track of their
lifetime on the client::

    factory = ResourceFactory('http://localhost:8000/api/v1/')

    class SomeResource(factory.some_resource):

        def __init__(self, *args, **kwargs):
            super(SomeResource, self).__init__(*args, **kwargs)
            # This is a field in the DB model:
            self.alive = True

        def __del__(self):
            self.alive = False
            self.save()

And then you can use the derived class as you would any class returned from the
:py:class:`~tastytopping.ResourceFactory`::

    new_resource = SomeResource(field1='value1', field2=2).save()


Ignore MultipleResourcesReturned when creating a Resource
---------------------------------------------------------

So, you've arrived here after getting a
:py:class:`~tastytopping.exceptions.MultipleResourcesReturned` exception
when trying to create a new Resource (or maybe you're just reading through the
docs)? This section goes through what happens when creating a Resource without
a unique field set, and what you can do about it.

Take a Resource whose only unique field is the auto-incrementing ``id`` field.
Assuming the Resource has ``always_return_data = False``, then creating two
resources as below will create some problems::

    factory.another_resource(name='Bob').save()
    factory.another_resource(name='Bob').save()

The second :py:meth:`~tastytopping.resource.Resource.save` will raise a
:py:class:`~tastytopping.exceptions.MultipleResourcesReturned` exception. This
happens because TastyTopping will attempt to GET the newly created resource.
The response, however, will return two resources, which means TastyTopping
can't be sure which one it created.

As suggested by the exception, one easy way around this, especially if you
don't use the Resources after creating them, is to use
::py:meth:`~tastytopping.resource.Resource.create`::

    factory.another_resource.create([
        {'name': 'Bob'},
        {'name': 'Bob'},
    ])

No attempt will be made to GET the resources after POSTing them, so the problem
won't be encountered.

The other solution presented by the exception is to explicitly ignore the
exception and GET the latest resource anyway::

    factory.another_resource(name='Bob').save()
    try:
        new_resource = factory.another_resource(name='Bob').save()
    except MultipleResourcesReturned:
        new_resource = factory.another_resource.filter(name='Bob').latest()

Be warned, though, that this should only be done if you are SURE that no other
Resource was created in the meantime, either in another thread, another
process, or another machine.
