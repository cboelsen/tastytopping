from django.conf.urls import patterns, url, include
from tastypie.api import Api

from .api import TestResource, UserResource, ApiKeyResource, NoFilterResource, TreeResource


api_v1 = Api(api_name='v1')
api_v1.register(TestResource())
api_v1.register(UserResource())
api_v1.register(ApiKeyResource())
api_v1.register(NoFilterResource())
api_v1.register(TreeResource())


urlpatterns = patterns('',
    url(r'^api/', include(api_v1.urls)),
)
