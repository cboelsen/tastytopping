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
    NoUniqueFilterableFields,
    FieldNotNullable,
    FieldNotInSchema,
    FilterNotAllowedForField,
    BadRelatedType,
    NoResourcesExist,
    MultipleResourcesReturned,
    RestMethodNotAllowed,
    ResourceDeleted,
    CreatedResourceNotFound,
    BadJsonResponse,
    ErrorResponse,
    NonExistantResource,
    CannotConnectToAddress,
)

from .factory import ResourceFactory
