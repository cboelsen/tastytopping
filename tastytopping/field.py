from datetime import datetime

from . import tastytypes


class Field(object):

    def __init__(self, value):
        self._value = value
        self._str = value

    def stream(self):
        return self._str

    def value(self):
        return self._value

    def filter(self, field):
        return field, self._str


class DateTimeField(Field):

    def __init__(self, value):
        if isinstance(value, datetime):
            self._value = value
            self._str = value.strftime(tastytypes.DATETIME_FORMAT1)
        else:
            self._str = value
            # Try with milliseconds, otherwise without.
            try:
                self._value = datetime.strptime(value, tastytypes.DATETIME_FORMAT1)
            except ValueError:
                self._value = datetime.strptime(value, tastytypes.DATETIME_FORMAT2)


class ResourceField(Field):

    def __init__(self, value, factory):
        if hasattr(value, 'uri'):
            self._value = value
        else:
            resource_type = self._get_resource_type(value)
            resource_class = getattr(factory, resource_type)
            self._value = resource_class(_fields=value)

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

    def __init__(self, values, factory):
        self._value = [ResourceField(v, factory) for v in values]

    def stream(self):
        return [v.stream() for v in self._value]

    def value(self):
        return [v.value() for v in self._value]

    def filter(self, field):
        related_field = self._value[0].value().filter_field()
        return '{0}__{1}'.format(field, related_field), [getattr(v.value(), related_field) for v in self._value]

# TODO Add a method for streaming GET requests (no uri allowed).

def create_field(field, field_type, factory):
    if field is None:
        return Field(None)

    if field_type == tastytypes.RELATED:
        if hasattr(field, 'split') or hasattr(field, 'uri'):
            result = ResourceField(field, factory)
        else:
            result = ResourceListField(field, factory)
    elif field_type == tastytypes.DATETIME:
        result = DateTimeField(field)
    else:
        result = Field(field)
    return result
