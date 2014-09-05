# -*- coding: utf-8 -*-

"""
.. module: factory
    :platform: Unix, Windows
    :synopsis: Create classes to access the API's resources.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('ResourceFactory', )


from threading import Lock


from .api import TastyApi
from .resource import Resource


class ResourceFactory(object):
    """Create classes with which to access the API's resources.

    The resource classes are accessed as member variables on the factory object,
    via a resource's name. For example, with a resource at
    ``http://localhost/app_name/api/v1/example_resource/``, the ResourceFactory
    will have a member variable called 'example_resource' returning a
    :py:class:`~tastytopping.resource.Resource` class (more specifically, a
    subclass of it, specialised for the resource in question)::

        >>> factory = ResourceFactory('http://localhost/app_name/api/v1/')
        >>> old_resource = factory.example_resource.get(name='bob')
        >>> new_resource = factory.example_resource(name='new name')
        >>> # And to see what resources are available:
        >>> factory.resources
        ['example', 'another_resource', 'entry']

    :param api_url: The url of the API!
    :type api_url: str
    :param verify: Sets whether SSL certificates for the API should be verified.
    :type verify: bool
    :var resources: (list) - The names of each
        :py:class:`~tastytopping.resource.Resource` this factory can create.
    """

    def __init__(self, api_url, verify=True):
        self._url = api_url
        self._dependencies = []

        api = TastyApi(api_url)
        api.verify = verify
        self.resources = api.resources()

        self.__dict__.update({k: None for k in self.resources})
        self._auth = None
        self._auth_lock = Lock()
        self._verify = verify

    def __getattribute__(self, name):
        if name not in ['resources', '_dependencies']:
            if name in self.resources:
                if self.__dict__[name] is None:
                    self.__dict__[name] = self._resource_class(name)
            else:
                for dep in self._dependencies:
                    if name in dep.resources:
                        return getattr(dep, name)
        return super(ResourceFactory, self).__getattribute__(name)

    def _resource_class(self, resource):
        return Resource._specialise(
            resource,
            {
                'api_url': self._url,
                'resource_name': resource,
                'auth': self._auth,
                'verify': self._verify,
                '_factory': self,
            },
        )

    def _get_auth(self):
        with self._auth_lock:
            return self._auth

    def _set_auth(self, auth):
        with self._auth_lock:
            self._auth = auth
            for resource_name in self.resources:
                getattr(self, resource_name).auth = auth

    auth = property(
        _get_auth,
        _set_auth,
        None,
        (
            '(:py:class:`~tastytopping.auth.AuthBase`) - '
            'Update the auth on all resources accessed via this API. '
            'Any new Resources will have their auth set to this value too.'
        ),
    )

    def add_factory_dependency(self, factory):
        """Add another ResourceFactory as a dependency.

        If any of the Resources associated with this ResourceFactory (Api on
        the tastypie side) have foreign keys to Resources associated with a
        different ResourceFactory, then this ResourceFactory depends on the
        other to create the Resources. In this case, you will need to pass the
        other ResourceFactory into this method.

        :param factory: The ResourceFactory that this depends on.
        :type factory: ResourceFactory
        """
        self._dependencies.append(factory)
