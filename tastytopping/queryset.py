# -*- coding: utf-8 -*-

"""
.. module: queryset
    :platform: Unix, Windows
    :synopsis: Provides a way to make lazy queries on Resources.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('QuerySet', 'EmptyQuerySet', )


import abc


from .exceptions import (
    MultipleResourcesReturned,
    NoResourcesExist,
    OrderByRequiredForReverse,
)
from .field import create_field


try:
    abc.ABC
except AttributeError:
    abc.ABC = abc.ABCMeta('ABC', (object, ), {})    # For python < 3.4


class _AbstractQuerySet(abc.ABC):

    def __init__(self, resource, **kwargs):
        self._resource = resource
        self._schema = resource._schema()
        self._api = resource._api()
        self._kwargs = kwargs
        self._reverse = kwargs.pop('__reverse', False)
        self._prefetch = kwargs.pop('__prefetch', [])
        self._ordering = kwargs.pop('order_by', [])
        if not isinstance(self._ordering, list):
            self._ordering = [self._ordering]
        self._count = None

        self._val_retriever = None
        self._retrieved_resources = []
        self._prefetched_resources = {k: None for k in self._prefetch}

    @abc.abstractmethod
    def __and__(self, other):
        raise NotImplementedError()

    def __bool__(self):
        return self.exists()

    # TODO Eventually remove: This is only for python2.x compatability
    __nonzero__ = __bool__

    @classmethod
    @abc.abstractmethod
    def _queryset_class(cls):
        raise NotImplementedError()

    def filter(self, **kwargs):
        """Return a new QuerySet, with the given filters additionally applied.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: A new QuerySet.
        :rtype: QuerySet
        """
        new_kwargs = self._kwargs.copy()
        new_kwargs.update(kwargs)
        if '__reverse' not in new_kwargs:
            new_kwargs['__reverse'] = self._reverse
        if self._ordering or 'order_by' in new_kwargs:
            new_kwargs['order_by'] = self._ordering + new_kwargs.get('order_by', [])
        if self._prefetch or '__prefetch' in new_kwargs:
            new_kwargs['__prefetch'] = self._prefetch + new_kwargs.get('__prefetch', [])
        return self._queryset_class()(self._resource, **new_kwargs)

    def all(self):
        """Returns a copy of this QuerySet.

        :returns: A new QuerySet.
        :rtype: QuerySet
        """
        return self.filter()

    def none(self):
        """Return an EmptyQuerySet object."""
        return EmptyQuerySet(self._resource, **self._kwargs)

    def get(self, **kwargs):
        """Return an existing object via the API.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: The resource identified by the kwargs.
        :rtype: :py:class:`~tastytopping.resource.Resource`
        :raises: :py:class:`~tastytopping.exceptions.NoResourcesExist`,
            :py:class:`~tastytopping.exceptions.MultipleResourcesReturned`
        """
        # No more than two results are needed, so save the server's resources.
        kwargs['limit'] = 2
        resource_iter = self.filter(**kwargs).iterator()
        try:
            result = next(resource_iter)
        except StopIteration:
            raise NoResourcesExist(self._resource._name(), self._kwargs, kwargs)
        try:
            next(resource_iter)
            raise MultipleResourcesReturned(self._resource._name(), self._kwargs, kwargs)
        except StopIteration:
            pass
        return result

    @abc.abstractmethod
    def update(self, **kwargs):
        """Abstract method"""
        raise NotImplementedError()

    @abc.abstractmethod
    def delete(self):
        """Abstract method"""
        raise NotImplementedError()

    def order_by(self, *args):
        """Order the query's result according to the fields given.

        The first field's order will be most important, with the importance
        decending thereafter. Calling this method multiple times will achieve
        the same. For example, the following are equivalent::

            query = query.order_by('path', 'content')
            # Is equivalent to:
            query = query.order_by('path')
            query = query.order_by('content')

        :param args: The fields according to which to order the Resources.
        :type args: tuple
        :returns: A new QuerySet.
        :rtype: QuerySet
        """
        return self.filter(order_by=list(args))

    def exists(self):
        """Returns whether this query matches any resources.

        :returns: True if any resources match, otherwise False.
        :rtype: bool
        """
        return self.count() > 0

    @abc.abstractmethod
    def count(self):
        """Abstract method"""
        raise NotImplementedError()

    def reverse(self):
        """Reverse the order of the Resources returned from the QuerySet.

        Calling reverse() on an alerady-reversed QuerySet restores the original
        order of Resources.

        Evaluating a QuerySet that is reversed but has no order will result in
        a :py:class:`~tastytopping.exceptions.OrderByRequiredForReverse`
        exception being raised. So, ensure you call
        :py:meth:`~tastytopping.queryset.QuerySet.order_by` on any reversed
        QuerySet.

        :returns: A new QuerySet.
        :rtype: QuerySet
        """
        return self.filter(__reverse=self._reverse ^ True)

    @abc.abstractmethod
    def iterator(self):
        """Abstract method"""
        raise NotImplementedError()

    @abc.abstractmethod
    def latest(self, field_name):
        """Abstract method"""
        raise NotImplementedError()

    @abc.abstractmethod
    def earliest(self, field_name):
        """Abstract method"""
        raise NotImplementedError('abstract')

    def first(self):
        """Return the first resource from the query.

        :returns: The first Resource, or None if the QuerySet is empty.
        :rtype: :py:class:`~tastytopping.resource.Resource`
        """
        try:
            return self[0]
        except IndexError:
            return None

    def last(self):
        """Works like :meth:`~tastytopping.queryset.QuerySet.first`, but returns
        the last resource.
        """
        try:
            return self[-1]
        except IndexError:
            return None

    def prefetch_related(self, *args):
        """Returns a QuerySet that will automatically retrieve, in a single
        batch, related objects for each of the specified lookups.

        This method simulates an SQL 'join' and including the fields of the
        related object, except that it does a separate lookup for each
        relationship and does the ‘joining’ in Python.

        It will check that the related field hasn't already been 'joined' by
        setting 'full=True' in the Resource's field in tastypie.

        Take note that this method will fetch all the resources of all the
        given fields to do the 'joining', so it only makes sense for QuerySets
        that will return a large nunmber of resources. Even then, watch the
        memory usage!

        :param args: The fields to prefetch.
        :type args: tuple
        :returns: A new QuerySet.
        :rtype: QuerySet
        """
        return self.filter(__prefetch=list(args))

    def __getstate__(self):
        state = self.__dict__.copy()
        state['_resource'] = state['_resource']()
        # TODO Keep cached copies?!
        del state['_val_retriever']
        del state['_retrieved_resources']
        del state['_prefetched_resources']
        return state

    def __setstate__(self, state):
        state['_resource'] = type(state['_resource'])
        for member, value in state.items():
            setattr(self, member, value)
        self._val_retriever = None
        self._retrieved_resources = []
        self._prefetched_resources = {k: None for k in self._prefetch}


class QuerySet(_AbstractQuerySet):
    """Allows for easier querying of resources while reducing API access.

    The API and function are very similar to Django's
    `QuerySet <https://docs.djangoproject.com/en/dev/ref/models/querysets/>`_
    class. There are a few differences: slicing this QuerySet will always
    evaluate the query and return a list; and this QuerySet accepts negative
    slices/indices [#f1]_.

    Note that you normally wouldn't instantiate QuerySets yourself; you'd be
    using a Resource's :meth:`~tastytopping.resource.Resource.filter`,
    :meth:`~tastytopping.resource.Resource.all`,
    :meth:`~tastytopping.resource.Resource.none`,
    :meth:`~tastytopping.resource.Resource.get` methods to create a QuerySet.

    A quick example::

        # These will not evaluate the query (ie. hit the API):
        some_resources_50_100 = SomeResource.filter(rating__gt=50, rating__lt=100)
        some_resources_ordered = some_resources_50_100.order_by('rating')

        # These will evaluate the query:
        first_resource_above_50 = some_resources_ordered.first()
        arbitrary_resource_between_50_and_100 = some_resources_ordered[5]
        all_resources_between_50_and_100 = list(some_resources_ordered)
        every_third_resource_between_100_and_50 = some_resources_ordered[::-3]

.. [#f1] Using negative slices/indices will result in more requests to the API, as
        the QuerySet needs to find the number of resources this query matches (using
        :py:meth:`~tastytopping.queryset.QuerySet.count`).
    """

    @staticmethod
    def _create_filter_list(val1, val2):
        make_set = lambda val: list([val]) if not isinstance(val, list) else set(val)
        val1 = make_set(val1)
        val2 = make_set(val2)
        return list(val1 & val2)

    def __and__(self, other):
        if not isinstance(other, _AbstractQuerySet):
            raise TypeError('Expected instance of type "{0}"; found "{1}".'.format(type(self), type(other)))
        if not self._resource._name() == other._resource._name():
            raise TypeError(
                'Expected query against "{0}"; found "{1}".'.format(
                    type(self._resource._name()),
                    type(other._resource._name()),
                )
            )
        if isinstance(other, EmptyQuerySet):
            return EmptyQuerySet(other._resource)
        new_kwargs = self._kwargs.copy()
        if self._ordering or other._ordering:
            new_kwargs['order_by'] = self._ordering + other._ordering
        new_kwargs['__reverse'] = self._reverse
        for name, value in other._kwargs.items():
            if name in new_kwargs:
                new_kwargs[name] = self._create_filter_list(new_kwargs[name], value)
            else:
                new_kwargs[name] = value
        return QuerySet(self._resource, **new_kwargs)

    def __getitem__(self, key):
        # TODO Cache the results here too!
        if isinstance(key, slice):
            if key.start is None and key.stop is None:
                return list(self)
            if key.start is not None and key.start == key.stop:
                return []
            try:
                resource_list = self._get_specified_resources(key.start, key.stop, key.step or 1)
            except IndexError:
                resource_list = []
            resource_list = [self._insert_prefetched_resources(r) for r in resource_list]
            return resource_list
        elif isinstance(key, int):
            stop = key - 1 if key < 0 else key + 1
            try:
                resource = self._get_specified_resources(key, stop)[0]
            except IndexError:
                raise IndexError("The index {0} is out of range.".format(key))
            resource = self._insert_prefetched_resources(resource)
            return resource
        else:
            raise TypeError("Invalid argument type.")

    def __iter__(self):
        for resource in self._retrieved_resources:
            resource = self._insert_prefetched_resources(resource)
            yield resource
        for resource in self._retriever():
            resource = self._insert_prefetched_resources(resource)
            self._retrieved_resources.append(resource)
            yield resource

    @classmethod
    def _queryset_class(cls):
        return QuerySet

    def _prefetch_resources(self, related_resource, field_name):
        all_related_resource = []
        for resources in related_resource._api().paginate(related_resource._full_name(), limit=0):
            all_related_resource += resources['objects']
        self._prefetched_resources[field_name] = {r['resource_uri']: r for r in all_related_resource}

    def _insert_prefetched_resources(self, resource):
        for pre_field_name in self._prefetched_resources:
            related_resource = getattr(resource, pre_field_name, None)
            # See if the field is a Resource, and check that the fields aren't already populated.
            if hasattr(related_resource, 'uri') and not related_resource._resource_fields:
                # Preload the related resources if it hasn't already happened.
                if not self._prefetched_resources[pre_field_name]:
                    self._prefetch_resources(related_resource, pre_field_name)
                # Create a new prefetched field to replace the old field.
                details = self._prefetched_resources[pre_field_name][related_resource.uri()]
                full_related_resource = create_field(details, None, self._resource._factory).value()
                setattr(resource, pre_field_name, full_related_resource)
            elif isinstance(related_resource, list) and len(related_resource) > 0:
                # Preload the related resources if it hasn't already happened.
                if not self._prefetched_resources[pre_field_name]:
                    self._prefetch_resources(related_resource[0], pre_field_name)
                # Create a list of new prefetched fields to replace the old fields.
                full_related_resources = []
                for rel in related_resource:
                    details = self._prefetched_resources[pre_field_name][rel.uri()]
                    full_related_resources.append(create_field(details, None, self._resource._factory).value())
                setattr(resource, pre_field_name, full_related_resources)
        return resource

    def _filter_fields(self, fields):
        filtered_fields = {}
        for name, value in fields.items():
            if isinstance(value, _AbstractQuerySet):
                value = list(value.all())
            field_desc = self._schema.field(name)
            field_type = field_desc and field_desc['type']
            relate_name, relate_field = create_field(value, field_type, self._resource._factory).filter(name)
            filtered_fields[relate_name] = relate_field
        return filtered_fields

    def _convert_to_positive_indices(self, start, stop, step):
        start = start or 0
        stop = stop or 0
        if start < 0 or stop < 0:
            total_count = self.count()
            if start < 0:
                start = total_count + start
            if stop < 0:
                stop = total_count + stop
            if stop < 0:
                raise IndexError()
            if start < 0:
                start = 0
        if step < 0:
            start, stop = stop + 1, start + 1
        return start, stop

    def _get_specified_resource_objects(self, start, limit):
        get_kwargs = self._kwargs.copy()
        get_kwargs.update({'offset': start, 'limit': limit})
        get_kwargs = self._apply_order(get_kwargs)
        get_kwargs = self._filter_fields(get_kwargs)
        all_resources = []
        for resources in self._api.paginate(self._resource._full_name(), **get_kwargs):
            all_resources += resources['objects']
            result = resources
        total_count = result['meta']['total_count']
        self._count = total_count
        return all_resources

    def _get_specified_resources(self, start, stop, step=1):
        start, stop = self._convert_to_positive_indices(start, stop, step)
        available = len(self._retrieved_resources)
        if start < available and stop < available and stop != 0:
            return self._retrieved_resources[start:stop:step]
        limit = stop - start if stop > start else start - stop
        objects = self._get_specified_resource_objects(start, limit)[::step]
        return create_field(objects, None, self._resource._factory).value()

    def _retriever(self):
        if self._val_retriever is None:
            self._val_retriever = self.iterator()
        return self._val_retriever

    @staticmethod
    def _flip_field_order(field):
        return field[1:] if field.startswith('-') else '-' + field

    def _apply_order(self, kwargs):
        if self._ordering:
            ordered_kwargs = kwargs.copy()
            ordering = self._ordering if not self._reverse else [self._flip_field_order(o) for o in self._ordering]
            ordered_kwargs['order_by'] = ordering
            return ordered_kwargs
        else:
            if self._reverse:
                raise OrderByRequiredForReverse(self._resource, self._kwargs)
            return kwargs

    def count(self):
        """Return the number of records for this resource.

        :param kwargs: Keywors arguments to filter the search.
        :type kwargs: dict
        :returns: The number of records for this resource.
        :rtype: int
        """
        if self._count is None:
            count_kwargs = self._kwargs.copy()
            count_kwargs['limit'] = 1
            self._schema.check_list_request_allowed('get')
            count_kwargs = self._filter_fields(count_kwargs)
            response = self._api.get(self._resource._full_name(), **count_kwargs)
            self._count = response['meta']['total_count']
        return self._count

    def update(self, **kwargs):
        """Updates all resources matching this query with the given fields.

        This method provides a large optimization to updating each resource
        individually: This method will only make 2 API calls per thousand
        resources.

        :param kwargs: The fields to update: {field_name: field_value, ...}
        :type kwargs: dict
        """
        resources_to_update = list(self)
        resources = []
        for resource in resources_to_update:
            resource_fields = kwargs.copy()
            resource_fields['resource_uri'] = resource.uri()
            resources.append(resource_fields)
        self._resource.bulk(create=resources)

    def delete(self):
        """Delete every Resource filtered by this query.

        Note that there is an optimization when calling delete() on a full
        QuerySet (ie. one without filters). So:

        ::

            # this will be quicker:
            Resource.all().filter()
            # than this:
            Resource.filter(id__gt=0).filter()
        """
        if self._kwargs:
            resources = list(self)
            self._resource.bulk(delete=resources)
        else:
            # If no filters have been given, then we can shortcut to delete the list resource.
            self._schema.check_list_request_allowed('delete')
            self._api.delete(self._resource._full_name())
            self._resource._alive = set()

    def iterator(self):
        """Returns an iterator to the QuerySet's results.

        Evaluates the QuerySet (by performing the query) and returns an
        iterator over the results. A QuerySet typically caches its results
        internally so that repeated evaluations do not result in additional
        queries. In contrast, iterator() will read results directly, without
        doing any caching at the QuerySet level (internally, the default
        iterator calls iterator() and caches the return value). For a QuerySet
        which returns a large number of objects that you only need to access
        once, this can result in better performance and a significant reduction
        in memory.

        Note that using iterator() on a QuerySet which has already been
        evaluated will force it to evaluate again, repeating the query.

        :returns: An iterator to the QuerySet's results.
        :rtype: iterator object
        """
        self._schema.check_list_request_allowed('get')
        self._schema.check_fields_in_filters(self._kwargs)
        fields = self._filter_fields(self._kwargs)
        fields = self._apply_order(fields)
        if 'limit' not in fields:
            fields['limit'] = 0
        for response in self._api.paginate(self._resource._full_name(), **fields):
            for obj in response['objects']:
                yield self._resource(_fields=obj)
            self._count = response['meta']['total_count']

    def _return_first_by_date(self, field_name):
        date_kwargs = self._kwargs.copy()
        date_kwargs['__reverse'] = self._reverse
        date_field = field_name if not self._reverse else self._flip_field_order(field_name)
        date_kwargs['order_by'] = [date_field] + self._ordering
        try:
            return QuerySet(self._resource, **date_kwargs)[0]
        except IndexError:
            raise NoResourcesExist(self._resource._name(), self._kwargs)

    def latest(self, field_name):
        """Returns the latest resource, by date, using the 'field_name'
        provided as the date field.

        Note that :meth:`~tastytopping.queryset.QuerySet.earliest` and
        :meth:`~tastytopping.queryset.QuerySet.latest` exist purely for
        convenience and readability.

        :param field_name: The name of the field to order the resources by.
        :type field_name: str
        :returns: The latest resource, by date.
        :rtype: :py:class:`~tastytopping.resource.Resource`
        :raises: :py:class:`~tastytopping.exceptions.NoResourcesExist`
        """
        field_name = self._flip_field_order(field_name)
        return self._return_first_by_date(field_name)

    def earliest(self, field_name):
        """Works otherwise like :meth:`~tastytopping.queryset.QuerySet.latest`
        except the direction is changed.
        """
        return self._return_first_by_date(field_name)


class EmptyQuerySet(_AbstractQuerySet):
    """A no-op QuerySet class to shortcut API access."""

    def __and__(self, other):
        return EmptyQuerySet(self._resource)

    def __getitem__(self, key):
        raise IndexError("The index {0} is out of range.".format(key))

    def __iter__(self):
        return self.iterator()

    @classmethod
    def _queryset_class(cls):
        return EmptyQuerySet

    def count(self):
        return 0

    def update(self, **kwargs):
        pass

    def delete(self):
        pass

    def iterator(self):
        return iter([])

    def latest(self, field_name):
        raise NoResourcesExist(self._resource._name(), self._kwargs)

    def earliest(self, field_name):
        raise NoResourcesExist(self._resource._name(), self._kwargs)
