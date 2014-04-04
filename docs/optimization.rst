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
:py:meth:`~tastytopping.resource.Resource.bulk` method, with convenience
methods provided for readability and ease of use
(:py:meth:`~tastytopping.resource.Resource.create`,
:py:meth:`~tastytopping.queryset.QuerySet.update`,
:py:meth:`~tastytopping.queryset.QuerySet.delete`,
). To create multiple blogentries (from the tutorial)::

    factory.entry.create([
        {user=user1, title='Entry 1', body='Some text.\n'},
        {user=user1, title='Entry 2', body='More text.\n'},
        {user=user2, title='Entry 3', body='This text.\n'},
        {user=user1, title='Entry 4', body='... text.\n'},
    ])

Note that unlike when creating a resource normally, the
:py:meth:`~tastytopping.resource.Resource.create` method does NOT return
anything. This means if you want to get any of the resources later, you'll need
to :py:meth:`~tastytopping.resource.Resource.get` them.

Using a :py:class:`~tastytopping.queryset.QuerySet`, it's also possible to
update multiple Resources in just two requests::

    queryset = factory.entry.filter(title__in=['Entry1', 'Entry2'])
    queryset.update(user=user2)

Note that while the update only takes a single request, there is a previous
request that will GET the relevant objects to update (seeing as it's not
possible to do it in one request like with SQL), because we need to know the
URIs of all relevant resources.

Lastly, it's possible to delete multiple Resources in two requests (GET and
PATCH like with :py:meth:`~tastytopping.queryset.QuerySet.update`)::

    # From the previous example.
    queryset.delete()

The exception to ``delete()`` requiring two requests is when the QuerySet
contains all resources (ie. you used
:py:meth:`~tastytopping.queryset.QuerySet.all`). Then a DELETE is sent to the
requests list view.

If you really needed to remove every last possible request, you can also
combine all the previous calls into a single bulk() call::

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


.. _prefetch_related:

Prefetching a QuerySet's related resources
------------------------------------------

For a :py:class:`~tastytopping.queryset.QuerySet` that returns a large number
of resources, it is sometimes more efficient to prefetch some, or all, of the
resources' related resources. This can be achieved using a QuerySet's
:py:meth:`~tastytopping.queryset.QuerySet.prefetch_related` method, which will
GET all resources of the given type in a single request and perform an
SQL-type 'join'.

Take the example below, which will loop through all collections (a made-up
resource that contains many blog entries) and print the title of each blog
entry in the collection::

    collection_queryset = factory.collection.all()
    for collection in collection_queryset:
        for entry in collection.entries:
            print(entry.title)

In this case, there will be an initial GET request for the collections,
followed by a GET request for each ``entry`` in the collection. Ouch!

To get around this situation, you can call
:py:meth:`~tastytopping.queryset.QuerySet.prefetch_related` on the initial
QuerySet::

    collection_queryset = factory.collection.all()
    collection_queryset.prefetch_related('entries')
    for collection in collection_queryset:
        for entry in collection.entries:
            print(entry.title)

This time, there will be a grand total of two GET requests: one for the
collections, and one for the entries.

There is a trade-off with this method, though, and that is that every resource
of the requested type will be prefetched. This means that if you only need to
prefetch a few resources, or there are a lot of resources of the requested
type, then it can also be detrimental to call
:py:meth:`~tastytopping.queryset.QuerySet.prefetch_related`.


Server-side
-----------

There are several ways to reduce the number of requests sent to the API by
setting up your tastypie Resources (possibly) differently. As always, don't use
these suggestions where they don't make sense (ie. use your brain!).

max_limit
^^^^^^^^^

In a tastypie Resource, there is a member of the ``Meta`` class called
``max_limit``. Because TastyTopping only fetches the resources which were
queried, it's advisable to set this to ``0``, to minimise requests sent (or at
least sufficiently large, if not unlimited). The ``limit`` member should still
be set to a reasonably small value (like the default of ``20``), since that is
used when iterating over a QuerySet.

always_return_data
^^^^^^^^^^^^^^^^^^

Setting ``always_return_data = True`` will ensure a resource's details are
returned from a POST request when creating it. If this is set to ``False``,
TastyTopping needs to transmit another GET request when a Resource's fields are
accessed.
