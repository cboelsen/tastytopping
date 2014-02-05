from .field import create_field


class NestedResource(object):

    def __init__(self, uri, api, schema, factory, **kwargs):
        self.api = api
        self.uri = uri if uri.endswith('/') else uri + '/'
        self.schema = schema
        self.factory = factory
        self.kwargs = kwargs

    def __getattr__(self, name):
        return NestedResource(self.uri + name, self.api, self.schema, self.factory)

    def __call__(self, *args, **kwargs):
        uri = self._append_url(*args)
        return NestedResource(uri, self.api, self.schema, self.factory, **kwargs)

    def _append_url(self, *args):
        args_string = '/'.join(str(a) for a in args)
        return '{0}{1}'.format(self.uri, args_string)

    def get(self, **kwargs):
        kwargs = kwargs or self.kwargs
        result = self.api.nested(self.uri, **kwargs)
        return create_field(result, None, self.factory).value()

    def post(self, **kwargs):
        kwargs = kwargs or self.kwargs
        result = self.api.post(self.uri, **kwargs)
        return create_field(result, None, self.factory).value()

    def put(self, **kwargs):
        kwargs = kwargs or self.kwargs
        result = self.api.put(self.uri, **kwargs)
        return create_field(result, None, self.factory).value()
