#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: skip-file


import unittest

from tastytopping import *

from . import run_testsite


FACTORY = ResourceFactory('http://localhost:8111/test/api/v1/')

################################ BAD RESOURCES ################################
NoFilterResource = FACTORY.no_filter


############################### GOOD RESOURCES ################################
ApiKeyResource = FACTORY.api_key
TestResource = FACTORY.test_resource
TestTreeResource = FACTORY.tree

class TestResourceDerived(TestResource):
    pass


################################# TEST CLASS ##################################
class TestsBase(unittest.TestCase):

    ############### CONSTANTS ##############
    TEST_PATH1 = u'tést1üö'
    TEST_PATH2 = u'tést2ßä'
    TEST_RATING1 = 43
    TEST_USERNAME = 'testuser'
    TEST_API_KEY = ApiKeyResource.get(user__username='testuser').key

    ################ HELPERS ###############
    def setUp(self):
        TestResource.auth = HTTPApiKeyAuth(self.TEST_USERNAME, self.TEST_API_KEY)
        self._delete_all_test_objects()
        self._default_auth = TestResource.auth

    def tearDown(self):
        TestResource.auth = self._default_auth

    def _delete_all_test_objects(self):
        TestResource.all().delete()
        self._delete_all(TestTreeResource)

    def _delete_all(self, resource_class):
        try:
            for resource in resource_class.all():
                try:
                    resource.delete()
                except ResourceDeleted:
                    pass
        except NoResourcesExist:
            pass

    def _delete(self, res):
        res._api().delete(res.full_uri())


try:
    FACTORY.user.auth = HTTPSessionAuth()
    raise StandardError('Should not have been allowed to use Session auth before getting a CSRF token!')
except MissingCsrfTokenInCookies:
    pass

TestResource.auth = HTTPApiKeyAuth(TestsBase.TEST_USERNAME, TestsBase.TEST_API_KEY)
FACTORY.user.nested.login(username=TestsBase.TEST_USERNAME, password='password').post()
FACTORY.user.auth = HTTPSessionAuth()

CACHE = (
    TestResource(path='cache1'),
    TestResourceDerived(path='cache3'),
    TestTreeResource(name='cache4'),
    FACTORY.user.get(username='testuser')
)
