# -*- coding: utf-8 -*-

"""
.. module: schema
    :platform: Unix, Windows
    :synopsis: Wrap a resource's schema to separate functionality.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('TastySchema', )


from .exceptions import (
    ReadOnlyField,
    NoUniqueFilterableFields,
    FieldNotNullable,
    RestMethodNotAllowed,
    NoFiltersInSchema,
    FieldNotInSchema,
    FilterNotAllowedForField,
    InvalidFieldName,
    NoDefaultValueInSchema,
)


_ALL = 1
_ALL_WITH_RELATIONS = 2
_POSSIBLE_FILTERS = [
    'exact',
    'iexact',
    'contains',
    'icontains',
    'in',
    'gt',
    'gte',
    'lt',
    'lte',
    'startswith',
    'istartswith',
    'endswith',
    'iendswith',
    'range',
    'year',
    'month',
    'day',
    'week_day',
    'hour',
    'minute',
    'second',
    'isnull',
    'search',
    'regex',
    'iregex',
]


class TastySchema(object):
    """Wraps a resource's schema.

    :param api: A TastyApi object connected to the appropriate address.
    :type api: TastyApi
    :param resource: The resource name.
    :type resource: str
    """

    def __init__(self, data, resource):
        self._resource = resource
        self._schema = data
        self._check_schema()

    def __str__(self):
        return str(self._schema) if self._schema else repr(self)

    def __repr__(self):
        return '<Schema for "{0}">'.format(self._resource)

    def _check_request_allowed(self, req_type, req):
        key = 'allowed_{0}_http_methods'.format(req_type)
        req = req.lower()
        if req not in self._schema[key]:
            error = (
                "Resource '{0}' does not allow '{1}'. Allowed are '{2}': {3}"
                "".format(self._resource, req, key, self._schema[key])
            )
            raise RestMethodNotAllowed(error)

    def _fields(self):
        return self._schema['fields']

    def _filters(self):
        try:
            return self._schema['filtering']
        except KeyError:
            raise NoFiltersInSchema(self._schema)

    def _check_filter(self, field):
        if field in ['limit', 'order_by']:
            return
        try:
            field_name, filter_type = field.split('__')
            allowed_filters = self._filters()[field_name]
            if _ALL != allowed_filters and _ALL_WITH_RELATIONS != allowed_filters:
                if filter_type in _POSSIBLE_FILTERS and filter_type not in allowed_filters:
                    raise FilterNotAllowedForField(field, self._schema)
        except ValueError:  # No filter_type to check.
            self._filters()[field.split('__', 1)[0]]  # Check that the field can be filtered on. # pylint: disable=W0106

    def _check_schema(self):
        invalid_names = set(['limit', 'order_by'])
        field_names = set(self._fields().keys())
        invalid_field_names = field_names & invalid_names
        if invalid_field_names:
            raise InvalidFieldName(list(invalid_field_names))

    def filterable_key(self):
        """Return a field that both: has unique values; and can be filtered on (defaults to 'id').

        :returns: The name of the field.
        :rtype: str
        :raises: NoUniqueFilterableFields
        """
        if 'id' in self._filters():
            return 'id'
        # Try to find any other unique field that can be filtered on.
        for field, desc in self._fields().items():
            if desc['unique'] and field in self._filters():
                return field
        error = "No unique fields can be filtered for '{0}'. Schema: {1}".format(self._resource, self._schema)
        raise NoUniqueFilterableFields(error)

    def validate(self, field, value):
        """Check that the schema does not prohibit the given value in the given field.

        :raises: FieldNotNullable, ReadOnlyField
        """
        schema_field = self.field(field)
        if schema_field is None:
            return  # We can't validate the field as it's not in the schema.
        if value is None and not schema_field['nullable']:
            raise FieldNotNullable(self._resource, field)
        if schema_field['readonly']:
            raise ReadOnlyField(self._resource, field)

    def field(self, name):
        """Return the description of the given field.

        :param name: Field name.
        :type name: str
        :returns: The description of the given field {str: str}.
        :rtype: dict
        """
        return self._fields().get(name)

    def default(self, field):
        """Return the default value for this field."""
        field_desc = self.field(field)
        if field_desc is None:
            raise FieldNotInSchema(field, self._schema)
        value = field_desc['default']
        if value == "No default provided.":
            if field_desc['blank']:
                value = ""
            elif field_desc['nullable']:
                value = None
            else:
                raise NoDefaultValueInSchema(field)
        return value

    def check_list_request_allowed(self, req):
        """Check that the schema allows the given REST method for 'allowed_list_http_methods'.

        :raises: RestMethodNotAllowed
        """
        self._check_request_allowed('list', req)

    def check_detail_request_allowed(self, req):
        """Check that the schema allows the given REST method for 'allowed_detail_http_methods'.

        :raises: RestMethodNotAllowed
        """
        self._check_request_allowed('detail', req)

    def remove_fields_not_in_filters(self, fields):
        """Return a dict of fields and value that can be used as filters.

        :param fields: the fields and values to filter on.
        :type fields: dict {str: obj}
        :returns: the given fields, minus those that can't be used as filters.
        :rtype: dict {str: obj}
        :raises: FilterNotAllowedForField
        """
        if not fields:
            return fields
        filters = self._filters().copy()
        filters.update({'limit': 0, 'order_by': 0})
        result = {}
        for field, value in fields.items():
            for fil in filters:
                if field.split('__')[0] == fil:
                    self._check_filter(field)
                    result[field] = value
                    break
        return result

    def check_fields_in_filters(self, fields):
        """Check that all fields are valid filters.

        :param fields: the fields and values to filter on.
        :type fields: dict {str: obj}
        :raises: FilterNotAllowedForField
        """
        allowed_fields = self.remove_fields_not_in_filters(fields)
        bad_fields = set(fields.keys()) - set(allowed_fields.keys())
        if bad_fields:
            raise FilterNotAllowedForField(bad_fields, self._schema)

    @staticmethod
    def _help_filtering(filtering, field):
        try:
            fil = filtering[field]
            if fil is 1:
                fil = 'All filtering allowed'
            elif fil is 2:
                fil = 'All filtering allowed including relations'
        except (KeyError, AttributeError):
            fil = 'Cannot filter'
        return fil

    @staticmethod
    def _help_description(description):
        if description == 'A date & time as a string. Ex: "2010-11-10T03:07:43"':
            description = 'A python datetime object. Ex: datetime.datetime.now()'
        elif description == ('Many related resources. Can be either a list of URIs '
                             'or list of individually nested resource data.'):
            description = 'Many related resources. Takes a list of Resources.'
        elif description == 'A single related resource. Can be either a URI or set of nested resource data.':
            description = 'A single related resource. Takes a Resource.'
        return description

    @staticmethod
    def _help_methods(methods):
        method_text = ''
        for method in methods:
            method_text += method.upper() + ', '
        method_text = method_text[:-2] if method_text else ''
        return method_text

    def help(self, verbose):
        """Returns a string containing the help text for this resource.

        :param verbose: whether to return the lengthy help text or not.
        :type verbose: bool
        :returns: help text
        :rtype: unicode
        """
        related_type = lambda desc: '{0} ({1})'.format(desc['type'], desc['related_type'])
        filtering = self._schema.get('filtering')
        fields = self._fields().items()
        ordering = self._schema.get('ordering')
        help_text = (
            'Resource "{0}"\n'
            '================{1}\n\n'
            'Default format returned : {2}\n'
            'Allowed list methods    : {3}\n'
            'Allowed detail methods  : {4}\n'
            'Ordering                : {5}\n'
            ''.format(
                self._resource,
                '=' * len(self._resource),
                self._schema.get('default_format'),
                self._help_methods(self._schema.get('allowed_list_http_methods')),
                self._help_methods(self._schema.get('allowed_detail_http_methods')),
                ordering if ordering else 'Not allowed'
            )
        )
        help_text += '\nFields\n------\n'
        for field, desc in fields:
            if verbose:
                help_text += (
                    '\n{0}\n'
                    '{1}\n'
                    'Description : {2}\n'
                    'Type        : {3}\n'
                    'Filtering   : {9}\n'
                    'Default     : {8}\n'
                    'Extra       : Readonly   Unique    Blank      Null\n'
                    '                 {4}         {5}         {6}         {7}\n'
                    ''.format(
                        field,
                        '^' * len(field),
                        self._help_description(desc['help_text']),
                        desc['type'] if desc['type'] != 'related' else related_type(desc),
                        'x' if desc['readonly'] else ' ',
                        'x' if desc['unique'] else ' ',
                        'x' if desc['blank'] else ' ',
                        'x' if desc['nullable'] else ' ',
                        desc['default'] if desc['default'] else "''",
                        self._help_filtering(filtering, field),
                    )
                )
            else:
                help_text += '{0} [{1}] -- {2}\n'.format(
                    field,
                    desc['type'] if desc['type'] != 'related' else related_type(desc),
                    self._help_description(desc['help_text']),
                )
        return help_text
