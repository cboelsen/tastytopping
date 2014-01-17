# -*- coding: utf-8 -*-

"""
.. module: factory
    :platform: Unix, Windows
    :synopsis: Create classes to access the API's resources.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('ResourceFactory', )


from .api import Api
from .resource import ListResource


class ResourceFactory(object):

    def __init__(self, api_url):
        self._api = Api(api_url)

    def __getattr__(self, name):
        return ListResource(name, self._api)
