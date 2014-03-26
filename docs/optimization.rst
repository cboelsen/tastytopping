.. _optimization:

Optimization
============

Because TastyTopping communicates over the network to a tastypie API,
operations are expensive. Care has been taken to only prod the API when needed,
but when dealing with thousands of resources a bit of extra help would be nice.
Thankfully, there are a few ways to optimize these network accesses.

Bulk operations (PATCH)
-----------------------

The PATCH REST method provides a nice way to for clients to create, update and
delete resources en masse, which tastypie has implemented. TastyTopping has
wrapped this functionality behind the
:py:meth:`~tastytopping.resource.Resource.bulk` method. To create multiple blog
entries (from the tutorial):

::

    factory.entry.bulk(create=[
        {user=user1, title='Entry 1', body='Some text.\n'},
        {user=user1, title='Entry 2', body='More text.\n'},
        {user=user2, title='Entry 3', body='This text.\n'},
        {user=user1, title='Entry 4', body='... text.\n'},
    ])

Note that unlike when creating a resource normally, the bulk method does NOT
return anything. This means if you want to get any of the resources later,
you'll need to :py:meth:`~tastytopping.resource.Resource.get` them.

Using bulk, it's also possible to update multiple Resources in a single
request:

::

    entry1 = factory.entry.get(title='Entry1')
    entry2 = factory.entry.get(title='Entry2')
    entry1.user = entry2.user = user2
    factory.entry.bulk(update=[entry1, entry2])

Lastly, it's possible to delete multiple Resources in a single request:

::

    factory.entry.bulk(delete=[entry1, entry2])

If you really needed to remove every last possible request, you can also
combine all the previous calls into a single bulk() call:

::

    entry3 = factory.entry.get(title='Entry3')
    entry4 = factory.entry.get(title='Entry4')
    entry3.user = user1
    factory.entry.bulk(create=[
            {user=user1, title='Entry 5', body='Some text.\n'},
            {user=user1, title='Entry 6', body='More text.\n'},
        ],
        update=[entry3],
        delete=[entry4]
    )

You might now be thinking that this sounds pretty good. You might even be
thinking that you'll use this wherever possible. Well, there is a single,
potentially bad, downside: Because of the potentially large size of bulk
updates, the API will respond with a 202 before completing the request (see
`wikipedia <http://en.wikipedia.org/wiki/List_of_HTTP_status_codes#2xx_Success>`_,
and `tastypie <http://django-tastypie.readthedocs.org/en/latest/interacting.html#bulk-operations>`_).
This means it's possible for the request to fail without us knowing. However,
in the event that it does fail, all changes will be rolled back.

Delete list resource
--------------------

To prevent you having to call :py:meth:`~tastytopping.resource.Resource.delete`
for every resource in a list resource, you can instead use the QuerySet's
:py:meth:`~tastytopping.queryset.QuerySet.delete` method:

::

    entry1 = factory.entry(user=user1, title='Entry 1', body='Some text.\n')
    entry2 = factory.entry(user=user1, title='Entry 2', body='Some text.\n')
    factory.entryall().delete()

This method will also mark all Resources as deleted, so any use of them will
result in a ResourceDeleted exception.

Update multiple fields
----------------------

As a shortcut, it's possible to update multiple fields in a single request
using :py:meth:`~tastytopping.resource.Resource.update`, which will also update
the resource remotely (ie. effectively call
:py:meth:`~tastytopping.resource.Resource.save`).

::

    entry1.update(
        user=user2,
        title='Different title',
        body='Different text',
    )
