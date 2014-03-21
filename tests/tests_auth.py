#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: skip-file


import unittest

from tastytopping import *

from .tests_base import *


################################# TEST CLASS ##################################
class AuthTests(TestsBase):

    def test_unset_auth___exception_raised(self):
        TestResource.auth = None
        self.assertRaises(ErrorResponse, TestResource(path=self.TEST_PATH1).save)

    def test_change_auth_in_class___instances_change_auth(self):
        resource = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        TestResource.auth = None
        resource.rating = 20
        self.assertRaises(ErrorResponse, resource.save)

    def test_change_auth_in_base_class___instances_of_derived_classes_change_auth(self):
        resource = TestResourceDerived(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        TestResource.auth = None
        resource.rating = 20
        self.assertRaises(ErrorResponse, resource.save)

    def test_change_auth_in_one_class___only_instances_of_that_class_change_auth(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        TestTreeResource.auth = None
        self.assertEqual(resource1.rating, self.TEST_RATING1)

    def test_change_auth_in_base_class___derived_class_picks_up_changes(self):
        TestResourceDerived(path=self.TEST_PATH1, rating=self.TEST_RATING1)

    def test_change_auth_in_derived_class___base_classes_do_not_change_auth(self):
        TestResourceDerived.auth = None
        TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()

    def test_change_auth_in_derived_class___instances_of_base_classes_do_not_change_auth(self):
        resource = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        TestResourceDerived.auth = None
        resource.rating = 20

    def test_related_field_creation___resource_keeps_correct_auth(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        cont = FACTORY.container(test=res1).save()
        self.assertEqual(FACTORY.container.get().test.path, self.TEST_PATH1)

    def test_set_auth_on_factory___all_resources_created_in_factory_share_auth(self):
        new_factory = ResourceFactory('http://localhost:8111/test/api/v1')
        new_factory.auth = 4
        self.assertEqual(new_factory.auth, new_factory.test_resource.auth)
        self.assertEqual(new_factory.auth, new_factory.tree.auth)
        self.assertEqual(new_factory.auth, new_factory.user.auth)

    def test_change_auth_on_factory___all_resources_retrieved_from_factory_change_auth(self):
        new_factory = ResourceFactory('http://localhost:8111/test/api/v1')
        new_factory.test_resource.auth = 1
        new_factory.tree.auth = 2
        new_factory.auth = 3
        self.assertEqual(new_factory.auth, new_factory.test_resource.auth)
        self.assertEqual(new_factory.auth, new_factory.tree.auth)
