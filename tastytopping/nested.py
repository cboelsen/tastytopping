from .exceptions import (
    NonExistantResource,
    IncorrectNestedResourceArgs,
)
from .field import create_field


class NestedResource(object):

    def __init__(self, uri, api, schema, factory, **kwargs):
        self.api = api
        self.uri = uri if uri.endswith('/') else uri + '/'
        self.schema = schema
        self.factory = factory
        self.kwargs = kwargs
        self.get = self._nested_method(self.api.get)
        self.post = self._nested_method(self.api.post)
        self.put = self._nested_method(self.api.put)
        self.patch = self._nested_method(self.api.patch)
        self.delete = self._nested_method(self.api.delete)

    def __getattr__(self, name):
        return NestedResource(self.uri + name, self.api, self.schema, self.factory)

    def __call__(self, *args, **kwargs):
        uri = self._append_url(*args)
        return NestedResource(uri, self.api, self.schema, self.factory, **kwargs)

    def _append_url(self, *args):
        args_string = '/'.join(str(a) for a in args)
        return '{0}{1}'.format(self.uri, args_string)

    def _nested_method(self, method):
        def _api_method(**kwargs):
            kwargs = kwargs or self.kwargs
            try:
                result = method(self.uri, **kwargs)
            except NonExistantResource as err:
                raise IncorrectNestedResourceArgs(*err.args)
            return create_field(result, None, self.factory).value()
        return _api_method
