# -*- coding: utf-8 -*-

"""
.. module: factory
    :platform: Unix, Windows
    :synopsis: Create classes to access the API's resources.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('ResourceFactory', )


from .resource import Resource


class ResourceFactory(object):
    """Create classes with which to access the API's resources.

    The resource classes are accessed as member variables on the factory object,
    via a resource's name. For example, with a resource at
    http://localhost/app_name/api/v1/example_resource/, the ResourceFactory will
    have a member variable called 'example_resource' returning a
    :class:`tastytopping.resource.Resource` class (more specifically, a subclass
    of it, specialised for the resource in question):

    ::

        factory = ResourceFactory('http://localhost/app_name/api/v1/')
        old_resource = factory.example_resource.get(name='bob')
        new_resource = factory.example_resource(name='new name')

    :param api_url: The url of the API!
    :type api_url: str
    """

    def __init__(self, api_url):
        self._url = api_url
        self._classes = {}

    def __getattr__(self, name):
        return self._resource_class(name)

    def _resource_class(self, resource):
        try:
            return self._classes[resource]
        except KeyError:
            class _SpecificResource(Resource):
                api_url = self._url
                resource_name = resource
                _factory = self
            self._classes[resource] = _SpecificResource
            return _SpecificResource
