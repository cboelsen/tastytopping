API Documentation
=================

ResourceFactory
---------------

.. autoclass:: tastytopping.ResourceFactory
    :members:
    :undoc-members:

Resource
--------

.. autoclass:: tastytopping.resource.Resource
    :members: auth, uri, update, delete, refresh, save, fields, get, filter, all, bulk, create, none, check_alive
    :member-order: groupwise

QuerySet
--------

.. autoclass:: tastytopping.queryset.QuerySet
    :members: filter, all, none, get, update, delete, order_by, exists, count, reverse, iterator, latest, earliest, first, last, prefetch_related
    :member-order: groupwise

Authentications
---------------

.. automodule:: tastytopping.auth
    :members:
    :undoc-members:

Exceptions
----------

.. automodule:: tastytopping.exceptions
    :members:
    :undoc-members:
