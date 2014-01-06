# -*- coding: utf-8 -*-

"""
.. module: __init__
    :platform: Unix, Windows
    :synopsis: Publicise the public classes.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


from .auth import (
    AuthBase,
    HttpApiKeyAuth,
    HTTPBasicAuth,
    HTTPDigestAuth,
)

from .exceptions import (
    ReadOnlyField,
    FieldNotNullable,
    NoUniqueFilterableFields,
    RestMethodNotAllowed,
    NoFiltersInSchema,
    FieldNotInSchema,
    BadRelatedType,
    NoResourcesExist,
    MultipleResourcesReturned,
    FilterNotAllowedForField,
    InvalidFieldName,
    ResourceDeleted,
    CreatedResourceNotFound,
    BadJsonResponse,
    ErrorResponse,
    NonExistantResource,
    CannotConnectToAddress,
    IncorrectEndpointArgs,
    IncorrectEndpointKwargs,
)

from .factory import ResourceFactory
