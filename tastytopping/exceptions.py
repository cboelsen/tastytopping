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

class BadRelatedType(PrettyException):
    """Raised when a related field contains the wrong type."""
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



class ResourceDeleted(PrettyException):
    """Raised when attempting to use a deleted resource."""
    pass

class CreatedResourceNotFound(PrettyException):
    """Raised when no resource can be found matching the resource created."""



class BadJsonResponse(PrettyException):
    """Raised when the response cannot be JSON decoded."""
    pass

class ErrorResponse(PrettyException):
    """Raised when an error status is returned from the API."""
    pass

class NonExistantResource(PrettyException):
    """Raised when a non-existant resource has been given."""
    pass

class CannotConnectToAddress(PrettyException):
    """Raised when no connection was possible at the given address."""
    pass

class IncorrectEndpointArgs(PrettyException):
    """Raised when failing to GET a custom endpoint.

    This is caused by tastypie raising a NotFound error in a 202 response. The
    cause is (almost always) an incorrect number of args to the method.
    """
    pass

class IncorrectEndpointKwargs(PrettyException):
    """Raised when failing to GET a custom endpoint.

    Specifically, a MultiValueDictKeyError was raised in the custom endpoint.
    Since kwargs should have been passed to the Resource method, which
    the custom endpoint should be retrieving from the request.GET dict, it is
    assumed that kwargs were missing.
    """
    pass

