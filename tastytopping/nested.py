# -*- coding: utf-8 -*-

"""
.. module: nested
    :platform: Unix, Windows
    :synopsis: Allows nested resources to be called.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


from .exceptions import (
    NonExistantResource,
    IncorrectNestedResourceArgs,
    NoResourcesExist,
)
from .field import create_field


class NestedResource(object):
    """Allows a nested resource to be accessed from a standard resource.

    Nested resources are treated differently because they don't have a schema
    provided by tastypie. Consequently, the result has to be treated in a more
    generic way.
    """

    def __init__(self, uri, api, factory, **kwargs):
        self.api = api
        self.uri = uri if uri.endswith('/') else uri + '/'
        self.factory = factory
        self.kwargs = kwargs
        self.get = self._api_method(self.api.get, filter_fields=True)
        self.post = self._api_method(self.api.post)
        self.put = self._api_method(self.api.put)
        self.patch = self._api_method(self.api.patch)
        self.delete = self._api_method(self.api.delete)

    def __getattr__(self, name):
        return NestedResource(self.uri + name, self.api, self.factory)

    def __call__(self, *args, **kwargs):
        uri = self._append_url(*args)
        return NestedResource(uri, self.api, self.factory, **self._stream_fields(**kwargs))

    def _append_url(self, *args):
        args_string = '/'.join(str(a) for a in args)
        return '{0}{1}'.format(self.uri, args_string)

    def _stream_fields(self, **kwargs):
        fields = {}
        for name, value in kwargs.items():
            fields[name] = create_field(value, None, self._factory)
        return {n: v.stream() for n, v in fields.items()}

    def _filter_fields(self, **kwargs):
        fields = {}
        for name, value in kwargs.items():
            relate_name, relate_field = create_field(value, None, self._factory).filter(name)
            fields[relate_name] = relate_field
        return fields

    def _api_method(self, method, filter_fields=False):
        convert_fields = self._filter_fields if filter_fields else self._stream_fields
        def _api_method(**kwargs):
            kwargs = kwargs or self.kwargs
            try:
                result = method(self.uri, **convert_fields(**kwargs))
            except NonExistantResource as err:
                raise IncorrectNestedResourceArgs(*err.args)
            return create_field(result, None, self.factory).value()
        return _api_method

    def filter(self, **kwargs):
        """Return a list of Resources via the API, filtered by kwargs.

        Note that unlike when using the Resource class method, there is no
        guarantee that the API responds with a list of Resources at this
        endpoint. This means the user is responsible for ensuring this method
        is used at the correct endpoints.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        fields = self._filter_fields(**kwargs)
        exist = False
        for response in self.api.paginate(self.uri, **fields):
            for obj in response['objects']:
                yield create_field(obj, None, self.factory).value()
                exist = True
        if not exist:
            raise NoResourcesExist(self.uri, kwargs)

    def all(self):
        """Return a list of Resources via the API.

        Note that unlike when using the Resource class method, there is no
        guarantee that the API responds with a list of Resources at this
        endpoint. This means the user is responsible for ensuring this method
        is used at the correct endpoints.

        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        return self.filter()
