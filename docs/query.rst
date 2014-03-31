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

To view all available methods, take a look at the :doc:`tastytopping`.
