# -*- coding: utf-8 -*-

"""
.. module: field
    :platform: Unix, Windows
    :synopsis: Separates field_type-dependent functionality into Field classes.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('create_field', )


from datetime import datetime

from .exceptions import InvalidFieldValue
from . import tastytypes


class Field(object):
    """Wrap a field with a generic value."""

    def __init__(self, value):
        self._value = value
        self._str = value

    def stream(self):
        """Return the representation of this field that can be sent over HTTP."""
        return self._str

    def value(self):
        """Return the wrapped value."""
        return self._value

    def filter(self, field):
        """Return a (field_name, field_value) tuple for this field that can be
        used in GET requests.

        This method is exposed primarily because uris cannot be used for
        resources in GET requests in tastypie.
        """
        return field, self.stream()


class DateTimeField(Field):
    """Wrap a datetime field."""

    def __init__(self, value):
        if isinstance(value, datetime):
            value = value
            stream = value.strftime(tastytypes.DATETIME_FORMAT1)
        else:
            stream = value
            # Try with milliseconds, otherwise without.
            try:
                value = datetime.strptime(value, tastytypes.DATETIME_FORMAT1)
            except ValueError:
                value = datetime.strptime(value, tastytypes.DATETIME_FORMAT2)
        super(DateTimeField, self).__init__(value)
        self._str = stream


class ResourceField(Field):
    """Wrap a Resource in a to_one relationship."""

    def __init__(self, value, factory):
        if hasattr(value, 'uri'):
            value = value
        else:
            resource_type = self._get_resource_type(value)
            resource_class = getattr(factory, resource_type)
            value = resource_class(_fields=value)
        super(ResourceField, self).__init__(value)

    @staticmethod
    def _get_resource_type(details):
        try:
            return details['resource_uri'].split('/')[-3]
        except TypeError:
            return details.split('/')[-3]

    def stream(self):
        return self._value.uri()

    def filter(self, field):
        related_field = self._value.filter_field()
        return '{0}__{1}'.format(field, related_field), getattr(self._value, related_field)


class ResourceListField(Field):
    """Wrap a list of Resources in a to_many relationship."""

    def __init__(self, values, factory):
        value = [ResourceField(v, factory) for v in values]
        super(ResourceListField, self).__init__(value)

    def stream(self):
        return [v.stream() for v in self._value]

    def value(self):
        return [v.value() for v in self._value]

    def filter(self, field):
        try:
            related_field = self._value[0].value().filter_field()
            return '{0}__{1}'.format(field, related_field), [getattr(v.value(), related_field) for v in self._value]
        except IndexError:
            return field, []


def create_field(field, field_type, factory):
    """Create an appropriate Field based on the field_type."""

    if field is None:
        return Field(None)

    try:
        if field_type == tastytypes.RELATED:
            if hasattr(field, 'split') or hasattr(field, 'uri'):
                result = ResourceField(field, factory)
            else:
                result = ResourceListField(field, factory)
        elif field_type == tastytypes.DATETIME:
            result = DateTimeField(field)
        else:
            result = Field(field)
    except Exception as error:
        raise InvalidFieldValue(
            error,
            'Encountered "{0}" while creating a "{1}" Field with the value "{2}"'.format(error, field_type, field)
        )
    return result
