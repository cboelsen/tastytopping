from datetime import datetime


class WrongFieldError(Exception):
    pass


class Field(object):

    def __init__(self, field):
        self._value = field

    def stream(self):
        return self._value

    def value(self):
        return self._value


class DateTimeField(Field):

    def __init__(self, field):
        self._raw = field

        # Try with milliseconds, otherwise without.
        # TODO Yuck!
        try:
            self._value = datetime.strptime(self._raw, tastytypes.DATETIME_FORMAT1)
        except ValueError:
            try:
                self._value = datetime.strptime(self._raw, tastytypes.DATETIME_FORMAT2)
            except ValueError:
                raise WrongFieldError(self._raw)

    def stream(self):
        return self._raw

    def value(self):
        return self._value


class ResourceField(Field):

    def __init__(self, field, factory):
        if hasattr(field, 'uri'):
            self._value = field
        else:
            self._value = self._create_from_values(field, factory)

    @staticmethod
    def _get_resource_type(details):
        import sys
        sys.stderr.write('00ß00000000000000000000000 > ' + str(details))
        try:
            return details['resource_uri'].split('/')[-3]
        except TypeError:
            return details.split('/')[-3]

    def _create_from_values(self, field, factory):
        resource_type = self._get_resource_type(field)
        resource_class = getattr(factory, resource_type)
        return resource_class(_fields=field)

    def stream(self):
        return self._value.uri()

    def value(self):
        return self._value


class ResourceListField(Field):

    def __init__(self, fields, factory):
        self._value = self._create_from_values(fields, factory)
        self._raw = None

    @staticmethod
    def _create_from_values(fields, factory):
        return [ResourceField(f, factory).value() for f in fields]

    def stream(self):
        if self._raw is None:
            self._raw = [r.uri() for r in self.value()]
        return self._raw

    def value(self):
        return self._value
