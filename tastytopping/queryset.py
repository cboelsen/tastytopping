from .exceptions import (
    NoResourcesExist,
)
from .field import create_field


class QuerySet(object):

    def __init__(self, resource, schema, api, **kwargs):
        self._resource = resource
        self._schema = schema
        self._api = api
        self._ordering = kwargs.pop('order_by', [])
        if not isinstance(self._ordering, list):
            self._ordering = [self._ordering]
        self._kwargs = kwargs

        self._val_retriever = None
        self._retrieved_resources = []


    def __bool__(self):
        return self.count() > 0

    # TODO Eventually remove: This is only for python2.x compatability
    __nonzero__ = __bool__

    def __getitem__(self, key):
        # TODO Check if the resources have already been retrieved.
        if isinstance(key, slice):
            # TODO Handle step values.
            return self._get_specified_resources(key.start, key.stop)
        elif isinstance( key, int ):
            return self._get_specified_resources(key, key + 1)[0]
        else:
            raise TypeError("Invalid argument type.")

    def __iter__(self):
        exist = bool(self._retrieved_resources)
        for resource in self._retrieved_resources:
            yield resource
        for resource in self._retriever():
            self._retrieved_resources.append(resource)
            yield resource
            exist = True
        if not exist:
            raise NoResourcesExist(self._resource._name(), self._kwargs)

    # TODO This was taken straight from resource.py
    def _create_fields(self, **kwargs):
        fields = {}
        for name, value in kwargs.items():
            field_desc = self._schema.field(name)
            field_type = field_desc and field_desc['type']
            fields[name] = create_field(value, field_type, self._resource._factory)
        return fields

    # TODO This was taken straight from resource.py
    @staticmethod
    def _stream_fields(fields):
        return {n: v.stream() for n, v in fields.items()}

    def _get_specified_resources(self, start, stop):
        if start == stop:
            return []
        if start < 0:
            raise IndexError("The index {0} is out of range. Only positive indices are supported.".format(start))
        if stop < 0:
            raise IndexError("The index {0} is out of range. Only positive indices are supported.".format(stop))
        get_kwargs = self._kwargs.copy()
        get_kwargs.update({'offset': start, 'limit': stop - start})
        get_kwargs = self._apply_order(get_kwargs)
        get_kwargs = self._stream_fields(self._create_fields(**get_kwargs))
        result = self._api.get(self._resource.full_name(), **get_kwargs)
        total_count = result['meta']['total_count']
        if start >= total_count:
            raise IndexError("The index {0} is out of range.".format(start))
        if stop > total_count:
            raise IndexError("The index {0} is out of range.".format(stop))
        return create_field(result['objects'], None, self._resource._factory).value()

    def _retriever(self):
        if self._val_retriever is None:
            self._schema.check_fields_in_filters(self._kwargs)
            fields = {}
            for name, value in self._kwargs.items():
                field_desc = self._schema.field(name)
                field_type = field_desc and field_desc['type']
                relate_name, relate_field = create_field(value, field_type, self._resource._factory).filter(name)
                fields[relate_name] = relate_field
            self._schema.check_list_request_allowed('get')
            fields = self._apply_order(fields)
            fields = self._stream_fields(self._create_fields(**fields))
            def ret():
                for response in self._api.paginate(self._resource.full_name(), **fields):
                    for obj in response['objects']:
                        yield self._resource(_fields=obj)
            self._val_retriever = ret()
        return self._val_retriever

    def _apply_order(self, kwargs):
        if self._ordering:
            ordered_kwargs = kwargs.copy()
            ordered_kwargs['order_by'] = self._ordering
            return ordered_kwargs
        else:
            return kwargs

    def filter(self, **kwargs):
        """Return existing objects via the API, filtered by kwargs.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        new_kwargs = self._kwargs.copy()
        new_kwargs.update(kwargs)
        return QuerySet(self._resource, self._schema, self._api, **new_kwargs)

    def all(self):
        """Return all existing objects via the API.

        :returns: Resource objects.
        :rtype: list
        :raises: NoResourcesExist
        """
        return self.filter()

    def count(self):
        """Return the number of records for this resource.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: The number of records for this resource.
        :rtype: int
        """
        count_kwargs = self._kwargs.copy()
        count_kwargs['limit'] = 1
        self._schema.check_list_request_allowed('get')
        count_kwargs = self._stream_fields(self._create_fields(**count_kwargs))
        response = self._api.get(self._resource.full_name(), **count_kwargs)
        return response['meta']['total_count']

    def order_by(self, *args):
        """Order the query's result according to the fields given.
        
        The first field's order will be most important, with the importance
        decending thereafter. Calling this method multiple times will achieve
        the same. For example, the following are equivalent:

        ::

            query = query.order_by('path', 'content')
            # Is equivalent to:
            query = query.order_by('path')
            query = query.order_by('content')
        """
        return self.filter(order_by=self._ordering + list(args), **self._kwargs.copy())
