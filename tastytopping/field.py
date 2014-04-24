# -*- coding: utf-8 -*-

"""
.. module: field
    :platform: Unix, Windows
    :synopsis: Separates field_type-dependent functionality into Field classes.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('create_field', )


from datetime import datetime

from .exceptions import (
    InvalidFieldValue,
    BadUri,
)
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
                try:
                    value = datetime.strptime(value, tastytypes.DATETIME_FORMAT2)
                except ValueError:
                    value = datetime.strptime(value, tastytypes.DATETIME_FORMAT3)
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
        related_field = self.value().filter_field()
        filtered_field = self.value()._schema().append_to_filter(field, related_field)
        return filtered_field, getattr(self.value(), related_field)


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
            related_field = self.value()[0].filter_field()
            filtered_field = self.value()[0]._schema().append_to_filter(field, related_field)
            return filtered_field, [getattr(v, related_field) for v in self.value()]
        except IndexError:
            return field, []


class _FieldCreator(object):

    def __init__(self, field, field_type, factory):
        self._field = field
        self._field_type = field_type
        self._factory = factory

    def _is_probably_resource(self, field=None):
        if field is None:
            field = self._field
        return (
            hasattr(field, 'split') or
            hasattr(field, 'uri') or (
                isinstance(field, dict) and
                'resource_uri' in field
            )
        )

    def _is_probably_datetime(self):
        return (
            isinstance(self._field, datetime) or (
                hasattr(self._field, 'format') and
                self._field.count(':') == 2 and
                self._field.count('-') == 2 and
                self._field.count('T') == 1
            )
        )

    def _is_probably_resource_list(self):
        return (
            isinstance(self._field, list) and
            self._is_probably_resource(self._field[0])
        )


    def _try_remaining_types(self):
        if self._is_probably_datetime():
            return DateTimeField(self._field)
        else:
            return Field(self._field)

    def _create_guessed_field(self):
        try:
            if self._is_probably_resource():
                result = ResourceField(self._field, self._factory)
                result.value().full_uri()
            elif self._is_probably_resource_list():
                result = ResourceListField(self._field, self._factory)
                result.value()[0].full_uri()
            else:
                result = self._try_remaining_types()
        except (BadUri, IndexError, AttributeError):
            result = self._try_remaining_types()
        return result

    def _create_known_field(self):
        try:
            if self._field_type == tastytypes.RELATED:
                if self._is_probably_resource(self._field):
                    result = ResourceField(self._field, self._factory)
                else:
                    result = ResourceListField(self._field, self._factory)
            elif self._field_type == tastytypes.DATETIME:
                result = DateTimeField(self._field)
            else:
                result = Field(self._field)
        except Exception as error:
            raise InvalidFieldValue(
                error,
                'Encountered "{0}" while creating a "{1}" Field with the value "{2}"'.format(
                    error, self._field_type, self._field
                )
            )
        return result

    def create(self):
        """Create a Field object based on the construction params."""
        if self._field is None:
            return Field(None)
        if self._field_type is None:
            return self._create_guessed_field()
        return self._create_known_field()


def create_field(field, field_type, factory):
    """Create an appropriate Field based on the field_type."""

    creator = _FieldCreator(field, field_type, factory)
    return creator.create()
