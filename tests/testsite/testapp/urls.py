from django.conf.urls import patterns, url, include
from tastypie.api import Api

from .api import (
    TestResource,
    TestResource2,
    UserResource,
    ApiKeyResource,
    NoFilterResource,
    OnlyPostResource,
    TreeResource,
    TestContainerResource,
    InvalidFieldResource,
    NoUniqueInitFieldResource,
)


api_v1 = Api(api_name='v1')
api_v1.register(TestResource())
api_v1.register(UserResource())
api_v1.register(ApiKeyResource())
api_v1.register(NoFilterResource())
api_v1.register(OnlyPostResource())
api_v1.register(TreeResource())
api_v1.register(TestContainerResource())
api_v1.register(InvalidFieldResource())
api_v1.register(NoUniqueInitFieldResource())

api_v2 = Api(api_name='v2')
api_v2.register(TestResource2())


urlpatterns = patterns(
    '',
    url(r'^api/', include(api_v1.urls)),
    url(r'^api/', include(api_v2.urls)),
)
