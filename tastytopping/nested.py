from .field import create_field


class NestedResource(object):

    def __init__(self, uri, api, schema, factory, resource_type='list', **kwargs):
        self.api = api
        self.uri = uri if uri.endswith('/') else uri + '/'
        self.schema = schema
        self.factory = factory
        self.kwargs = kwargs
        self.method_check = self.schema.check_list_request_allowed if resource_type == 'list' else self.schema.check_detail_request_allowed

    def __getattr__(self, name):
        return NestedResource(self.uri + name, self.api, self.schema, self.factory)

    def __call__(self, *args, **kwargs):
        uri = self._append_url(*args)
        return NestedResource(uri, self.api, self.schema, self.factory, **kwargs)

    def _append_url(self, *args):
        args_string = '/'.join(str(a) for a in args)
        return '{0}{1}'.format(self.uri, args_string)

    def get(self, **kwargs):
        self.method_check('get')
        kwargs = kwargs or self.kwargs
        result = self.api.nested(self.uri, **kwargs)
        return create_field(result, None, self.factory).value()

    def post(self, **kwargs):
        self.method_check('post')
        kwargs = kwargs or self.kwargs
        result = self.api.post(self.uri, **kwargs)
        return create_field(result, None, self.factory).value()
