# -*- coding: utf-8 -*-

"""
.. module: objects
    :platform: Unix, Windows
    :synopsis: Provide the magic to attach the ORM to the API.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('Resource', )


from .exceptions import (
    NoResourcesExist,
    ResourceDeleted,
    NoResourcesExist,
)


class ResourceHasNoUri(Exception):
    pass


class Resource(object):

    _alive = set()

    def __init__(self, list_uri, api, **kwargs):
        self.__dict__['_fields'] = kwargs

        # TODO This is duplicated!
        self._uri = self._fields.get('resource_uri')
        if self._uri:
            self._alive.add(self._uri)

        self._api = api
        self._list_uri = list_uri
        self._full_uri_ = None
        self._type = None

    def __getattr__(self, name):
        self._check_alive()
        try:
            return self.fields()[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in self.fields():
            self._check_alive()
            self.fields()[name] = value
        else:
            super(Resource, self).__setattr__(name, value)

    def __bool__(self):
        return self.uri() in self._alive
    # TODO Eventually remove: This is only for python2.x compatability
    __nonzero__ = __bool__

    def _check_alive(self):
        try:
            if not self:
                raise ResourceDeleted(self.uri())
        except ResourceHasNoUri:
            pass

    def _full_uri(self):
        if self._full_uri_ is None:
            uri_cutoff = len(self.uri())
            while uri_cutoff:
                uri_cutoff -= 1
                if self._api.address().endswith(self.uri()[:uri_cutoff]):
                    return self._api.address() + self.uri()[uri_cutoff:]
            raise StandardError('Could not find full uri.')
        return self._full_uri_

    def fields(self):
        if not self._fields:
            self._fields = self._api.get(self._full_uri())
        return self._fields

    def uri(self):
        if self._uri is None:
            try:
                self._uri = self.fields()['resource_uri']
                self._alive.add(self._uri)
            except KeyError:
                raise ResourceHasNoUri()
        return self._uri

    def type(self):
        if self._type is None:
            self._type = self._full_uri()[len(self._api.address()):].split('/')[0]
        return self._type

    def delete(self):
        self._check_alive()
        self._api.delete(self._full_uri())
        self._alive.remove(self._uri)

    def refresh(self):
        self._fields = self._api.get(self._full_uri())

    def save(self):
        try:
            self.uri()
            self._check_alive()
            self._api.put(self._full_uri(), **self.fields())
        except ResourceHasNoUri:
            fields = self._api.post(self._list_uri, **self.fields())
            if not fields:
                fields = self.fields().copy()
                fields['limit'] = 2
                #fields = schema.remove_fields_not_in_filters(fields)
                # TODO Copied below from GET.
                result = self._api.get(self._list_uri, **fields)
                try:
                    self._fields = result['objects'][0]
                except IndexError:
                    raise NoResourcesExist()
            self._alive.add(self.uri())
        return self


class ListResource(object):

    def __init__(self, name, api):
        self._api = api
        self._uri = self._api.address() + name + '/'
        self._type = name

    def __call__(self, **kwargs):
        return Resource(self._uri, self._api, **kwargs)

    def uri(self):
        return self._uri

    def type(self):
        return self._type

    def get(self, **kwargs):
        result = self._api.get(self.uri(), **kwargs)
        objects = result['objects']
        # TODO Complain if more than one returned.
        try:
            return Resource(self._uri, self._api, **objects[0])
        except IndexError:
            raise NoResourcesExist()

    def count(self, **kwargs):
        kwargs['limit'] = 1
        result = self._api.get(self.uri(), **kwargs)
        return result['meta']['total_count']

    def delete(self):
        self._api.delete(self.uri())
