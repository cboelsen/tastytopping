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
)


class ResourceHasNoUri(Exception):
    pass


class Resource(object):

    def __init__(self, list_uri, api, **kwargs):
        self.__dict__['_fields'] = kwargs
        self._api = api
        self._list_uri = list_uri
        self._uri = None
        self._full_uri_ = None

    def __getattr__(self, name):
        try:
            return self.fields()[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in self.fields():
            self.fields()[name] = value
        else:
            super(Resource, self).__setattr__(name, value)

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
        return self._fields

    def uri(self):
        if self._uri is None:
            try:
                # TODO Add api.base_url to resource_uri.
                self._uri = self.fields()['resource_uri']
            except KeyError:
                raise ResourceHasNoUri()
        return self._uri

    def save(self):
        try:
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
        return self


class ListResource(object):

    def __init__(self, name, api):
        self._api = api
        self._uri = self._api.address() + name + '/'

    def __call__(self, **kwargs):
        return Resource(self._uri, self._api, **kwargs)

    def uri(self):
        return self._uri

    def get(self, **kwargs):
        result = self._api.get(self.uri(), **kwargs)
        objects = result['objects']
        try:
            return Resource(self._uri, self._api, **objects[0])
        except IndexError:
            raise NoResourcesExist()
