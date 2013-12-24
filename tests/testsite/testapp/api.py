from django.contrib.auth.models import User
from django.core import management

from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.models import ApiKey
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
    
from .models import Test, Tree


# Set up the DB the first time the DB is accessed.
management.call_command('syncdb', interactive=False)
management.call_command(
    'createsuperuser',
    username='testuser',
    email='none@test.test',
    interactive=False,
)
management.call_command('user')


class ApiKeyResource(ModelResource):
    class Meta:
        resource_name = 'api_key'
        queryset = ApiKey.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {'user': ALL_WITH_RELATIONS}


class UserResource(ModelResource):
    class Meta:
        resource_name = 'user'
        queryset = User.objects.all()
        excludes = ['email', 'password', 'is_superuser']
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {
            'username': ALL,
            'id': ALL,
        }
         
         
class TestResource(ModelResource):
    created_by = fields.ToOneField(UserResource, 'created_by', null=True)
    class Meta:
        queryset = Test.objects.all()
        resource_name = 'test_resource'
        list_allowed_methods   = ['get', 'post']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        filtering = {
            'path': [
                'exact',
                'iexact',
                'contains',
                'icontains',
                'in',
                'startswith',
                'endswith'
            ],
            'rating': [
                'exact',
                'in',
                'gt',
                'gte',
                'lt',
                'lte',
                'range',
                'isnull',
                'regex',
            ],
            'date': ALL,
            'title': ALL,
            'created_by': ALL_WITH_RELATIONS,
        }
        ordering = ['rating', 'date']


class NoFilterResource(ModelResource):
    class Meta:
        queryset = Test.objects.all()
        resource_name = 'no_filter'
        list_allowed_methods   = ['get', 'post']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        authorization = Authorization()
        filtering = {}


class TreeResource(ModelResource):
    parent = fields.ToOneField('self', 'parent', null=True)
    children = fields.ToManyField('self', 'children', null=True, related_name='parent')
    class Meta:
        resource_name = 'tree'
        queryset = Tree.objects.all()
        authorization = Authorization()
        always_return_data = True
        filtering = {
            'name': ALL,
            'parent': ALL_WITH_RELATIONS,
            'children': ALL_WITH_RELATIONS,
        }
