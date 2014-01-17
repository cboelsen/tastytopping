#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: skip-file

import datetime
import requests
import unittest

from tastytopping import *
from tastytopping.api import Api

from . import run_testsite


FACTORY = ResourceFactory('http://localhost:8111/test/api/v1')


################################# TEST CLASS ##################################
class IntegrationTest(unittest.TestCase):

    ############### CONSTANTS ##############
    TEST_PATH1 = u'tést1üö'
    TEST_PATH2 = u'tést2ßä'
    TEST_RATING1 = 43
    TEST_USERNAME = 'testuser'
    #TEST_API_KEY = ApiKeyResource.get(user__username='testuser').key

    ################ HELPERS ###############
    def setUp(self):
        requests.delete('http://localhost:8111/test/api/v1/test_resource/')

    def tearDown(self):
        pass

    ################# TESTS ################
    def test_resource_creation___fields_are_accessible(self):
        res = FACTORY.test_resource(path=self.TEST_PATH1)
        self.assertEqual(res.path, self.TEST_PATH1)

    def test_resource_creation___non_existent_field_raises_exception(self):
        res = FACTORY.test_resource(path=self.TEST_PATH1)
        self.assertRaises(AttributeError, getattr, res, 'path1')

    def test_get_empty_resource_list___exception_raised(self):
        self.assertRaises(NoResourcesExist, FACTORY.user.get, username='fake')

    def test_get_from_resource_list___resource_returned(self):
        res = FACTORY.user.get(username=self.TEST_USERNAME)
        self.assertEqual(res.username, self.TEST_USERNAME)

    def test_save_created_resource___resource_returned_from_get(self):
        res = FACTORY.test_resource(path=self.TEST_PATH1, rating=self.TEST_RATING1)
        res.save()
        self.assertEqual(FACTORY.test_resource.get(path=self.TEST_PATH1).rating, self.TEST_RATING1)

    def test_save_updated_resource___resource_fields_updated(self):
        res = FACTORY.test_resource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        res.rating = 12
        res.save()
        self.assertEqual(FACTORY.test_resource.get(path=self.TEST_PATH1).rating, 12)


if __name__ == "__main__":
    unittest.main()
