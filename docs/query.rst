.. _query:

QuerySets
=========

QuerySets are a way to contruct queries for a particular resource, while
minimising requests sent to the API. They function similarly to Django's
`QuerySets <https://docs.djangoproject.com/en/dev/ref/models/querysets/>`_,
so if you're comfortable with these you should be right at home with
TastyTopping's QuerySets (differences will be highlighted as you go).

Like Django's QuerySets, these will be evaluated only when needed - a term that
has a slightly different meaning here - in the following cases:

* **Iteration.** A QuerySet is iterable, and it executes its database query
  the first time you iterate over it.

* **Slicing / Indexing.** Unlike with Django's, TastyTopping's QuerySets are
  always evaluated when slicing or indexing.

* **list().** Same warnings apply as with Django's QuerySets - using
  ``list()`` will iterate over the whole QuerySet and load it into memory.

* **bool().** Testing a QuerySet in a boolean context, such as using
  ``bool()``, ``or``, ``and`` or an ``if`` statement, will cause the query to
  be executed.


Creation
--------

To create a :py:class:`~tastytopping.query.QuerySet`, it's usually easiest to
use one of the methods from :py:class:`~tastytopping.resource.Resource` which
returns a QuerySet for that Resource:

* :py:meth:`~tastytopping.resource.Resource.all` - return a QuerySet matching
  all objects of a particular Resource.

* :py:meth:`~tastytopping.resource.Resource.filter` - return a QuerySet
  matching objects filtered by the given keyword args. The filters used are the
  same as those passed to tastypie.

* :py:meth:`~tastytopping.resource.Resource.none` - return an EmptyQuerySet. It
  contains shortcuts to avoid hitting the API where necessary.


Usage
-----

To demonstrate using QuerySets, we're going to use the same API as in the
:doc:`tutorial` section::

    from tastytopping import ResourceFactory
    factory = ResourceFactory('http://127.0.0.1:8000/api/v1/')

We've even already used a QuerySet as part of the tutorial::

    existing_user = factory.user.all().first()

which is simple enough - it will get the first user (using the default
ordering). Using this existing user, we can query the API to see how many blog
entries this user has made::

    blog_entries = factory.entry.filter(user=existing_user)
    num_blog_entries = blog_entries.count()

To update the published date on all of these blog entries to the current date
in a single call::

    from datetime import datetime
    blog_entries.update(pub_date=datetime.now())

To delete all blog entries from before 2012::

    factory.entry.filter(pub_date__lt=datetime(2012)).delete()

There's a more convenient way to order the resources too; to order the blog
entries by reverse date::

    factory.entry.all().order_by('-pub_date')

or to get the latest blog entry::

    factory.entry.all().latest('pub_date')

There are some optimizations possible with QuerySets:

- :ref:`prefetch_related`.

To view all available methods, take a look at the :doc:`tastytopping`.
