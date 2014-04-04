.. _ref-tutorial:

Getting Started
===============

TastyTopping works together with a `Tastypie API
<http://django-tastypie.readthedocs.org/>`_ to easily access data remotely over
HTTP. What makes TastyTopping so useful is its simplicity.

This tutorial is designed to work with the simple blog application found in
Tastypie's `tutorial
<http://django-tastypie.readthedocs.org/en/latest/tutorial.html>`_. It also
assumes you have some knowledge of Tastypie, so if you're not clear on Django,
Tastypie, etc., then you'll probably want to look there first.


Installation
------------

Installation is the usual simple affair with python nowadays:

    1. Download the dependencies:

        - Python 2.7+ or Python 3.3+

        - requests 1.2.3+

    2. Either check out TastyTopping from `github
    <https://github.com/cboelsen/tastytopping>`_ or pull a release off
    `PyPI <https://pypi.python.org/pypi/TastyTopping/>`_:
    ``pip install tastytopping``.

Usage
-----

The :py:class:`tastytopping.ResourceFactory` class is how we will access our
API's resources. To begin with, it needs the URL of our API, which it takes in
its constructor. After that, resources are accessed as members of the factory.
Following Tastypie's simple blog application tutorial, let's add an entry to
the blog:

::

    from tastytopping import ResourceFactory
    factory = ResourceFactory('http://127.0.0.1:8000/api/v1/')
    # Get the first user (we don't mind which it is).
    existing_user = factory.user.all().first()
    new_entry = factory.entry(
        user=existing_user,
        title='New blog entry',
        body='Some text for the blog entry.\n'
    )
    new_entry.save()

To edit the blog entry at a later date, we simply need to edit the body field:

::

    new_entry.body += 'EDIT: Some more text!\n'
    new_entry.save()

Be aware that like the get() method on Django models,
:py:meth:`~tastytopping.resource.Resource.get()` expects a single result to be
returned, and will raise an exception otherwise (see
:py:class:`~tastytopping.exceptions.NoResourcesExist` and
:py:class:`~tastytopping.exceptions.MultipleResourcesReturned`).

Now that we've made the new blog entry, you'll probably notice it's not a very
good blog entry - let's get rid of it:

::

    new_entry.delete()

Beyond The Basics
-----------------

That's all there is to the basics of TastyTopping. It's simple, and hopefully
you'll find it useful.

That said, there is more to learn, if you need to use more of Tastypie's
features:

 - :doc:`query`

 - :doc:`auth`

 - :doc:`nested`

 - :doc:`optimization`

 - :doc:`cookbook`
