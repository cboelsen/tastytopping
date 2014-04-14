import json

from django.conf.urls import url
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core import management
from django.middleware.csrf import _get_new_csrf_key as get_new_csrf_key
from django.middleware.csrf import _sanitize_token, constant_time_compare

from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication, SessionAuthentication
from tastypie.authorization import Authorization
from tastypie.http import HttpGone, HttpMultipleChoices
from tastypie.models import ApiKey
from tastypie.resources import (
    ModelResource,
    ObjectDoesNotExist,
    MultipleObjectsReturned,
    ALL,
    ALL_WITH_RELATIONS,
)
from tastypie.utils import trailing_slash
    
from .models import Test, Tree, TestContainer, InvalidField, NoUniqueInitField


class ApiKeyResource(ModelResource):
    class Meta:
        resource_name = 'api_key'
        queryset = ApiKey.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {'user': ALL_WITH_RELATIONS}

    def get_schema(self, request, **kwargs):
        # Create an API key for testuser, and add a few extra users on first access.
        if not ApiKey.objects.exists():
            User.objects.create_user('testuser1', 'noemail1@nothing.com', 'password')
            User.objects.create_user('testuser2', 'noemail2@nothing.com', 'password')
            User.objects.create_user('testuser3', 'noemail3@nothing.com', 'password')
            User.objects.create_user('testuser4', 'noemail4@nothing.com', 'password')
            api_key = ApiKey.objects.get_or_create(user=User.objects.get(username='testuser'))
        return super(ApiKeyResource, self).get_schema(request, **kwargs)


class UserResource(ModelResource):
    class Meta:
        resource_name = 'user'
        queryset = User.objects.all()
        excludes = ['email', 'password', 'is_superuser']
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = SessionAuthentication()
        filtering = {
            'username': ALL,
            'id': ALL,
        }

    def prepend_urls(self):
        params = (self._meta.resource_name, trailing_slash())
        return [
            url(r"^(?P<resource_name>%s)/login%s$" % params, self.wrap_view('login'), name="api_login"),
            url(r"^(?P<resource_name>%s)/logout%s$" % params, self.wrap_view('logout'), name="api_logout")
        ]

    def login(self, request, **kwargs):
        """
        Authenticate a user, create a CSRF token for them, and return the user object as JSON.
        """
        self.method_check(request, allowed=['post'])
        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        username = data.get('username', '')
        password = data.get('password', '')

        if username == '' or password == '':
            return self.create_response(request, {
                'success': False,
                'error_message': 'Missing username or password'
            })

        u = User.objects.get(username='testuser')
        u.set_password('password')
        u.save()

        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                response = self.create_response(request, {
                    'success': True,
                    'username': user.username
                })
                response.set_cookie("csrftoken", get_new_csrf_key())
                return response
            else:
                return self.create_response(request, {
                    'success': False,
                    'reason': 'disabled',
                }, HttpForbidden)
        else:
            return self.create_response(request, {
                'success': False,
                'error_message': 'Incorrect username or password'
            })

    def logout(self, request, **kwargs):
        """
        Attempt to log a user out, and return success status.
        """
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        if request.user and request.user.is_authenticated():
            logout(request)
            return self.create_response(request, { 'success': True })
        else:
            return self.create_response(request, { 'success': False, 'error_message': 'You are not authenticated, %s' % request.user.is_authenticated() })
         
         
class TestResource(ModelResource):
    created_by = fields.ToOneField(UserResource, 'created_by', null=True)
    reviewed = fields.BooleanField(default=False, readonly=True)
    class Meta:
        queryset = Test.objects.all()
        resource_name = 'test_resource'
        list_allowed_methods   = ['get', 'post', 'patch', 'delete']
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


class OnlyPostResource(ModelResource):
    class Meta:
        queryset = Test.objects.all()
        resource_name = 'only_post'
        list_allowed_methods   = ['post']
        detail_allowed_methods = []
        authorization = Authorization()


class TreeResource(ModelResource):
    parent = fields.ToOneField('self', 'parent', null=True)
    children = fields.ToManyField('self', 'children', null=True, related_name='parent')
    class Meta:
        resource_name = 'tree'
        queryset = Tree.objects.all()
        list_allowed_methods   = ['get', 'post', 'patch']
        detail_allowed_methods = ['get', 'delete', 'put']
        authorization = Authorization()
        always_return_data = True
        max_limit = 10
        filtering = {
            'number': ALL,
            'name': ALL,
            'parent': ALL_WITH_RELATIONS,
            'children': ALL_WITH_RELATIONS,
        }

    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>{0})/(?P<pk>\w[\w/-]*)/depth{1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('calc_depth'),
                name="api_calc_depth",
            ),
            url(
                r'^(?P<resource_name>{0})/(?P<pk>\w[\w/-]*)/chained/nested/child{1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_child'),
                name="api_get_child",
            ),
            url(
                r'^(?P<resource_name>{0})/(?P<pk>\w[\w/-]*)/chained/nested/child_dict{1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_child_dict'),
                name="api_get_child_dict",
            ),
            url(
                r'^(?P<resource_name>{0})/(?P<pk>\w[\w/-]*)/nested_children{1}$'.format(self._meta.resource_name, trailing_slash()),
                self.children.to_class().wrap_view('get_list'),
                name="api_dispatch_detail",
            ),
            url(
                r'^(?P<resource_name>{0})/add/(?P<num1>\d+)/(?P<num2>\d+){1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('calc_add'),
                name="api_calc_add",
            ),
            url(
                r'^(?P<resource_name>{0})/mult{1}$'.format(self._meta.resource_name, trailing_slash()),
                self.wrap_view('calc_mult'),
                name="api_calc_mult",
            ),
        ]

    def calc_add(self, request, **kwargs):
        '''Return the sum of two numbers.'''
        self.method_check(request, allowed=['put'])
        total = int(kwargs['num1']) + int(kwargs['num2'])
        return self.create_response(request, total)

    def calc_mult(self, request, **kwargs):
        '''Return the product of two numbers.'''
        self.method_check(request, allowed=['post'])
        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        total = int(data['num1']) * int(data['num2'])
        return self.create_response(request, total)

    def get_child(self, request, **kwargs):
        """Return the first child of this resource."""
        self.method_check(request, allowed=['get'])
        try:
            bundle = self.build_bundle(data={'pk': kwargs['pk']}, request=request)
            obj = self.cached_obj_get(bundle=bundle, **self.remove_api_resource_names(kwargs))
            return self.create_response(request, self.get_resource_uri(obj.children.first()))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

    def get_child_dict(self, request, **kwargs):
        """Return the first child of this resource."""
        self.method_check(request, allowed=['get'])
        try:
            bundle = self.build_bundle(data={'pk': kwargs['pk']}, request=request)
            obj = self.cached_obj_get(bundle=bundle, **self.remove_api_resource_names(kwargs))
            bundle = self.build_bundle(obj=obj.children.first(), request=request)
            bundle = self.full_dehydrate(bundle)
            bundle = self.alter_detail_data_to_serialize(request, bundle)
            return self.create_response(request, bundle)
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

    def calc_depth(self, request, **kwargs):
        '''Return the depth of the tree node from the root.'''
        # This method includes the proper checks for use as a demonstration,
        # whereas the previous ones are merely cut-down test versions.
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


class InvalidFieldResource(ModelResource):
    class Meta:
        queryset = InvalidField.objects.all()
        resource_name = 'invalid_field'
        authorization = Authorization()


class NoUniqueInitFieldResource(ModelResource):
    class Meta:
        queryset = NoUniqueInitField.objects.all()
        resource_name = 'no_unique'
        authorization = Authorization()
        filtering = {'name': ALL,}
