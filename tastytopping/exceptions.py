# -*- coding: utf-8 -*-

"""
.. module: exceptions
    :platform: Unix, Windows
    :synopsis: A store of all exceptions to make importing them more convenient.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


import pprint


class PrettyException(Exception):
    """Ensure the JSON dicts fed into the exceptions are formatted nicely."""
    def __str__(self):
        error_text = '\n'
        for arg in self.args:
            if hasattr(arg, 'format'):
                error_text += '{0}\n'.format(arg)
            else:
                error_text += pprint.pformat(arg) + '\n'
        return error_text


class ReadOnlyField(PrettyException):
    """Raised when attempting to update a read-only field."""
    pass

class FieldNotNullable(PrettyException):
    """Raised when attempting to set a field to None, when the API forbids it."""
    pass

class NoUniqueFilterableFields(PrettyException):
    """Raised when the object has no fields with unique values to filter on."""
    pass

class RestMethodNotAllowed(PrettyException):
    """Raised when the API does not allow a certain REST method (get/post/put/delete)."""
    pass

class NoFiltersInSchema(PrettyException):
    """Raised when the resource has no filters listed in the schema."""
    pass

class FieldNotInSchema(PrettyException):
    """Raised when a field should be part of the resource's schema, but isn't."""
    pass

class InvalidFieldValue(PrettyException):
    """Raised when a field has been passed the wrong type."""
    pass

class NoResourcesExist(PrettyException):
    """Raised when getting resources, but none were found."""
    pass

class MultipleResourcesReturned(PrettyException):
    """Raised when more than one resource was found where only one was expected."""
    pass

class FilterNotAllowedForField(PrettyException):
    """Raised when the filter used is not in the list of filters for the field in the API."""
    pass

class InvalidFieldName(PrettyException):
    """Raised when a field name will cause unexpected behaviour.

    For instance, if a field is called 'limit', or 'order_by', it won't be
    possible to order or limit the search results.
    """
    pass

class NoDefaultValueInSchema(PrettyException):
    """Raised when a field has no default value, but the user asked for one.

    Note that this can happen if you haven't yet saved a Resource, and you're
    using a field that you haven't provided a value for. For instance:

    ::

        >>> res = factory.test_resource(path='test/path')
        >>> res.rating      # Exception raised if rating has no default value.
    """
    pass



class ResourceDeleted(PrettyException):
    """Raised when attempting to use a deleted resource."""
    pass

class CreatedResourceNotFound(PrettyException):
    """Raised when no resource can be found matching the resource created."""
    pass

class ResourceHasNoUri(PrettyException):
    """Raised when trying to use a not-yet-created Resource's uri().

    This can almost always be solved by saving the Resource first.
    """
    pass

class BadUri(PrettyException):
    """Raised when the URI given does not belong to the API."""
    pass




class ErrorResponse(PrettyException):
    """Raised when an error status is returned from the API."""
    pass

class CannotConnectToAddress(PrettyException):
    """Raised when no connection was possible at the given address."""
    pass

class IncorrectNestedResourceArgs(PrettyException):
    """Raised when failing to GET a nested resource.

    This is caused by tastypie raising a NotFound error in a 202 response. The
    cause is (almost always) an incorrect number of args to the method.
    """
    pass

class IncorrectNestedResourceKwargs(PrettyException):
    """Raised when failing to GET a nested resource.

    Specifically, a MultiValueDictKeyError was raised in the nested resource.
    Since kwargs should have been passed to the Resource method, which
    the nested resource should be retrieving from the request.GET dict, it is
    assumed that kwargs were missing.
    """
    pass



class MissingCsrfTokenInCookies(PrettyException):
    """Raised when no CSRF token could be found in a session's cookies.

    This exception normally occurs when no CSRF token was passed to a
    HTTPSessionAuth object and there was no user authentication prior (which
    returned a CSRF token)."""
    pass

class OrderByRequiredForReverse(PrettyException):
    """Raised by QuerySet when attempting to reverse a query without an order.

    This exception will be raised when attempting to evaluate a QuerySet that
    should be reversed (ie. reverse() has been called at least once), but does
    not have an order.
    """
