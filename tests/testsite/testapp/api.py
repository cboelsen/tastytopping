import json

from django.conf.urls import url
from django.contrib.auth.models import User
from django.core import management

from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.http import HttpGone, HttpMultipleChoices
from tastypie.models import ApiKey
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.utils import trailing_slash
    
from .models import Test, Tree, TestContainer


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
        list_allowed_methods   = ['get', 'post', 'patch']
        detail_allowed_methods = ['get', 'put', 'delete', 'patch']
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
        list_allowed_methods   = ['get', 'post']
        detail_allowed_methods = ['get', 'delete', 'put']
        authorization = Authorization()
        always_return_data = True
        filtering = {
            'name': ALL,
            'parent': ALL_WITH_RELATIONS,
            'children': ALL_WITH_RELATIONS,
        }

    def build_schema(self):
        data = super(TreeResource, self).build_schema()
        data['detail_endpoints'] = {
            'depth': self.calc_depth.__doc__,
        }
        data['list_endpoints'] = {
            'add': self.calc_add.__doc__,
            'mult': self.calc_mult.__doc__,
        }
        return data

    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>{0})/(?P<pk>\w[\w/-]*)/depth{1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('calc_depth'),
                name="api_calc_depth"
            ),
            url(
                r'^(?P<resource_name>{0})/add/(?P<num1>\d+)/(?P<num2>\d+){1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('calc_add'),
                name="api_calc_add"
            ),
            url(
                r'^(?P<resource_name>{0})/mult{1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('calc_mult'),
                name="api_calc_mult"
            ),
        ]

    def calc_add(self, request, **kwargs):
        '''Return the sum of two numbers.'''
        total = int(kwargs['num1']) + int(kwargs['num2'])
        return self.create_response(request, total)

    def calc_mult(self, request, **kwargs):
        '''Return the product of two numbers.'''
        total = int(request.GET['num1']) * int(request.GET['num2'])
        return self.create_response(request, total)

    def calc_depth(self, request, **kwargs):
        '''Return the depth of the tree node from the root.'''
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        try:
            bundle = self.build_bundle(data={'pk': kwargs['pk']}, request=request)
            obj = self.cached_obj_get(bundle=bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        depth = -1
        while obj:
            obj = obj.parent
            depth += 1

        self.log_throttled_access(request)
        return self.create_response(request, depth)


class TestContainerResource(ModelResource):
    test = fields.ToOneField(TestResource, 'test', null=True)
    class Meta:
        queryset = TestContainer.objects.all()
        resource_name = 'container'
        authorization = Authorization()
        filtering = {
            'id': ALL,
            'test': ALL_WITH_RELATIONS,
        }
