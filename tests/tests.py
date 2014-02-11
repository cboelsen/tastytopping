#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: skip-file

import copy
import datetime
import pickle
import requests
import unittest

from tastytopping import *
from tastytopping.api import TastyApi

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
class IntegrationTest(unittest.TestCase):

    ############### CONSTANTS ##############
    TEST_PATH1 = u'tést1üö'
    TEST_PATH2 = u'tést2ßä'
    TEST_RATING1 = 43
    TEST_USERNAME = 'testuser'
    TEST_API_KEY = ApiKeyResource.get(user__username='testuser').key

    ################ HELPERS ###############
    def setUp(self):
        TestResource.auth = HttpApiKeyAuth(self.TEST_USERNAME, self.TEST_API_KEY)
        TestTreeResource.caching = False
        FACTORY.user.caching = False
        self._delete_all_test_objects()
        self._default_auth = TestResource.auth

    def tearDown(self):
        TestResource.auth = self._default_auth

    def _delete_all_test_objects(self):
        TestResource.delete_all()
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
        res._api().delete(res._full_uri())

    ################# TESTS ################
    def test_create___object_returned_with_same_fields(self):
        resource = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        self.assertEqual(resource.path, self.TEST_PATH1)
        self.assertEqual(resource.rating, self.TEST_RATING1)

    def test_create_with_factory___object_returned_with_same_fields(self):
        factory = ResourceFactory('http://localhost:8111/test/api/v1')
        factory.test_resource.auth = HttpApiKeyAuth(self.TEST_USERNAME, self.TEST_API_KEY)
        resource = factory.test_resource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        self.assertEqual(resource.path, self.TEST_PATH1)
        self.assertEqual(resource.rating, self.TEST_RATING1)

    def test_get___same_object_returned_as_just_created(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        self.assertEqual(resource1.rating, resource2.rating)

    def test_set_value___value_set_in_new_get(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource1.rating = self.TEST_RATING1 + 1
        resource1.save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        self.assertEqual(resource2.rating, self.TEST_RATING1 + 1)

    def test_delete_object___no_object_to_get(self):
        resource = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource.delete()
        self.assertRaises(NoResourcesExist, list, TestResource.filter(path=self.TEST_PATH1))

    def test_delete_object_twice___exception_raised(self):
        resource = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource.delete()
        self.assertRaises(ResourceDeleted, resource.delete)

    def test_delete_then_access_member___exception_raised(self):
        resource = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource.delete()
        self.assertRaises(ResourceDeleted, getattr, resource, 'path')

    def test_delete_then_set_member___exception_raised(self):
        resource = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource.delete()
        self.assertRaises(ResourceDeleted, setattr, resource, 'path', self.TEST_PATH2)

    def test_cache_refresh___new_changes_picked_up(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        resource1.rating = 10
        resource1.save()
        resource2.refresh()
        self.assertEqual(resource1.rating, resource2.rating)

    def test_datetime_objects___streams_both_ways(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1)
        resource1.date = datetime.datetime(2013, 12, 6)
        resource1.save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        self.assertEqual(resource1.date, resource2.date)

    def test_datetime_objects_with_ms___streams_both_ways(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1)
        resource1.date = datetime.datetime(2013, 12, 6, 1, 1, 1, 500)
        resource1.save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        self.assertEqual(resource1.date, resource2.date)

    def test_switching_cache_off___values_pulled_directly_from_api(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        resource2.set_caching(False)
        resource1.rating = 10
        resource1.save()
        self.assertEqual(resource1.rating, resource2.rating)

    def test_switching_cache_back_on___values_become_stale(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        resource1.set_caching(False)
        resource2.set_caching(False)
        resource1.rating = 10
        self.assertEqual(resource1.rating, resource2.rating)
        resource2.set_caching(True)
        resource1.rating = 20
        self.assertNotEqual(resource1.rating, resource2.rating)

    def test_equality___objects_equal_when_uris_equal(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        self.assertEqual(resource1, resource2)

    def test_equality___objects_not_equal_when_uris_differ(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource2 = TestResource(path=self.TEST_PATH2, rating=self.TEST_RATING1).save()
        self.assertNotEqual(resource1, resource2)

    def test_equality___objects_not_equal_when_object_type_differ(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        self.assertFalse(resource1 == 1)

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

    def test_bad_address___exception_raised(self):
        factory = ResourceFactory('http://localhost:8888/test/api/v1')
        self.assertRaises(CannotConnectToAddress, factory.test_resource._schema)

    def test_bad_resource___exception_raised(self):
        self.assertRaises(NonExistantResource, FACTORY.not_exist, blah=1)

    def test_creating_with_fields_that_arent_filterable___fields_excluded_from_get(self):
        test_text = 'Text.'
        resource1 = TestResource(path=self.TEST_PATH1, text=test_text).save()
        self.assertEqual(test_text, resource1.text)

    def test_creating_resource_that_has_no_filters___object_created_but_exception_raised(self):
        self.assertRaises(CreatedResourceNotFound, NoFilterResource(path='a').save)
        self.assertEqual(next(iter(NoFilterResource.all())).path, 'a')

    def test_more_resources_to_get_than_default_limit___api_gets_all_resources(self):
        NUM_RESOURCES = 22
        resources = [{'path': self.TEST_PATH1 + str(i), 'rating': self.TEST_RATING1} for i in range(NUM_RESOURCES)]
        TestResource.bulk(create=resources)
        resources = TestResource.all()
        self.assertEqual(len(set(resources)), NUM_RESOURCES)

    def test_more_resources_to_get_than_given_limit___api_only_retrieve_up_to_limit(self):
        NUM_RESOURCES = 8
        LIMIT = 5
        resources = [{'path': self.TEST_PATH1 + str(i), 'rating': self.TEST_RATING1} for i in range(NUM_RESOURCES)]
        TestResource.bulk(create=resources)
        resources = TestResource.filter(limit=LIMIT)
        self.assertEqual(len(set(resources)), LIMIT)

    def test_order_by___resources_returned_in_order(self):
        TestResource(path=self.TEST_PATH1 + '1', rating=50).save()
        TestResource(path=self.TEST_PATH1 + '2', rating=40).save()
        TestResource(path=self.TEST_PATH1 + '3', rating=60).save()
        self.assertEqual(
            [60, 50, 40],
            [res.rating for res in TestResource.filter(order_by='-rating')]
        )
        self.assertEqual(
            [40, 50, 60],
            [res.rating for res in TestResource.filter(order_by='rating')]
        )

    def test_update_multiple_fields___single_request_for_all_updates(self):
        rating = 60
        title = 'TITLE'
        text = 'This is some text.'
        resource = TestResource(path=self.TEST_PATH1, rating=40).save()
        resource.update(rating=rating, title=title, text=text)
        self.assertEqual(rating, resource.rating)
        self.assertEqual(title, resource.title)
        self.assertEqual(text, resource.text)

    def test_update_multiple_fields___all_fields_updated_remotely(self):
        rating = 60
        title = 'TITLE'
        text = 'This is some text.'
        resource = TestResource(path=self.TEST_PATH1, rating=40).save()
        resource.set_caching(False)
        resource.update(rating=rating, title=title, text=text)
        res2 = TestResource.get()
        self.assertEqual(rating, res2.rating)
        self.assertEqual(title, res2.title)
        self.assertEqual(text, res2.text)

    def test_update_with_field_not_in_schema___resource_updated(self):
        resource = TestResource(path=self.TEST_PATH1, rating=40).save()
        resource.fake = 'fake'
        self.assertTrue('fake' in resource.fields())

    def test_related_resource___basic_input_and_output_works(self):
        user = FACTORY.user.get(username=self.TEST_USERNAME)
        res = TestResource(path=self.TEST_PATH1, created_by=user).save()
        self.assertEqual(user, TestResource.get(path=self.TEST_PATH1).created_by)

    def test_post_resource_when_not_allowed___exception_raised(self):
        self.assertRaises(RestMethodNotAllowed, FACTORY.user, username='bob')

    def test_creating_resource_with_related_resource_members___accessed_via_tasty_objects(self):
        user = FACTORY.user.get(username=self.TEST_USERNAME)
        res = TestResource(path=self.TEST_PATH1, created_by=user).save()
        self.assertEqual(user.username, TestResource.get(path=self.TEST_PATH1).created_by.username)

    def test_creating_resource_with_related_resource_members___related_resource_works_with_class_members(self):
        user = FACTORY.user.get(username=self.TEST_USERNAME)
        res = TestResource(path=self.TEST_PATH1, created_by=user).save()
        res2 = TestResource.get(path=self.TEST_PATH1)
        FACTORY.user.caching = False
        self.assertFalse(res2.created_by.caching)

    def test_updating_related_resource___related_resource_updated(self):
        user = FACTORY.user.get(username=self.TEST_USERNAME)
        res = TestResource(path=self.TEST_PATH1).save()
        res.created_by = user
        res.save()
        self.assertEqual(user, TestResource.get(path=self.TEST_PATH1).created_by)

    def test_updating_incorrect_related_resource___exception_raised(self):
        res = TestResource(path=self.TEST_PATH1).save()
        self.assertRaises(InvalidFieldValue, setattr, res, 'created_by', 'user')

    def test_create_resource_with_multiple_resources_in_related_field___multiple_resources_accepted(self):
        tree1 = TestTreeResource(name='tree1')
        tree2 = TestTreeResource(name='tree2')
        parent = TestTreeResource(name='parent', children=[tree1, tree2])
        self.assertEqual(TestTreeResource.get(name='parent').children, [tree1, tree2])

    def test_update_resource_with_multiple_resources_in_related_field___multiple_resources_accepted(self):
        parent1 = TestTreeResource(name='parent1')
        parent2 = TestTreeResource(name='parent2')
        tree1 = TestTreeResource(name='tree1')
        tree2 = TestTreeResource(name='tree2')
        parent1.children = [tree1]
        parent1.children += [tree2]
        self.assertEqual(TestTreeResource.get(children=parent1.children).children, [tree1, tree2])

    def test_create_resource_with_same_parent_multiple_times___multiple_resources_returned_in_parent(self):
        root = TestTreeResource(name='root')
        tree1 = TestTreeResource(name='tree1', parent=root)
        tree2 = TestTreeResource(name='tree2')
        tree2.parent = root
        root.refresh()
        self.assertEqual(root.children, [tree1, tree2])

    def test_create_resource_with_explicitly_no_children___empty_list_accepted(self):
        root = TestTreeResource(name='root')
        root.children = []
        self.assertEqual(TestTreeResource.get(children=[]).name, 'root')

    def test_filter_types___gt_accepted(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=40).save()
        res2 = TestResource(path=self.TEST_PATH2, rating=35).save()
        res3 = TestResource.get(rating__gt=35)

    def test_filter_types___exact_accepted(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=40).save()
        res2 = TestResource(path=self.TEST_PATH2, rating=50).save()
        res3 = TestResource.get(rating__exact=40)

    def test_filter_types___contains_accepted(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        res3 = TestResource.get(path__contains=u'st1')

    def test_filter_types___in_accepted(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=10).save()
        res2 = TestResource(path=self.TEST_PATH2, rating=20).save()
        res3 = TestResource.get(rating__in=[10, 11, 12])

    def test_filter_types___startswith_accepted(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        res3 = TestResource.get(path__startswith=u'tést1')

    def test_filter_types_not_allowed___gt_rejected(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        self.assertRaises(FilterNotAllowedForField, TestResource.get, path__gt=u'a')

    def test_filter_types_not_allowed___startswith_rejected(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        self.assertRaises(FilterNotAllowedForField, TestResource.get, rating__startswith=1)

    def test_get_count_of_resource___number_of_resources_created_returned(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        self.assertEqual(len(TestResource), 2)
        res2 = TestResource(path='another_path').save()
        self.assertEqual(TestResource.count(), 3)

    def test_bool_value_of_resource_instance___true_when_exists_and_false_when_not(self):
        res = TestResource(path=self.TEST_PATH1).save()
        res_copy = TestResource.get(path=self.TEST_PATH1)
        self.assertTrue(res)
        self.assertTrue(res_copy)
        res.delete()
        self.assertFalse(res)
        self.assertFalse(res_copy)

    def test_resource_deleted_on_another_machine___exception_raised_when_updating(self):
        res = TestResource(path=self.TEST_PATH1).save()
        self._delete(res)
        res.rating = 50
        self.assertRaises(ResourceDeleted, res.save)

    def test_bulk_creation___multiple_resources_can_be_gotten(self):
        TestResource.bulk(create=[{'path': self.TEST_PATH1}, {'path': self.TEST_PATH2}])
        res1 = TestResource.get(path=self.TEST_PATH1)
        res2 = TestResource.get(path=self.TEST_PATH2)

    def test_bulk_delete___multiple_resources_deleted(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        TestResource.bulk(delete=[res1, res2])
        self.assertRaises(NoResourcesExist, list, TestResource.all())
        self.assertRaises(ResourceDeleted, setattr, res1, 'rating', 50)

    def test_get_with_multiple_results___throws_exception(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        self.assertRaises(MultipleResourcesReturned, TestResource.get)

    def test_queries_with_field_not_in_filters___throws_exception(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        self.assertRaises(FilterNotAllowedForField, TestResource.get, text=self.TEST_PATH1)

    def test_queries_with_non_existant_fields___throws_exception(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        self.assertRaises(FilterNotAllowedForField, TestResource.get, fake=self.TEST_PATH1)

    def test_queries_with_closely_related_non_existant_fields___throws_exception(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        self.assertRaises(FilterNotAllowedForField, TestResource.get, pat=self.TEST_PATH1)

    def test_related_field_creation___resource_keeps_correct_auth(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        cont = FACTORY.container(test=res1).save()
        self.assertEqual(FACTORY.container.get().test.path, self.TEST_PATH1)

    def test_caching_on_set___values_not_updated_before_save_called(self):
        TestResource.caching = True
        res1 = TestResource(path=self.TEST_PATH1).save()
        res1.rating = 40
        res1.text = 'TEXT!'
        self.assertNotEqual(TestResource.get(path=self.TEST_PATH1).rating, 40)
        self.assertNotEqual(TestResource.get(path=self.TEST_PATH1).text, 'TEXT!')

    def test_caching_on_set___values_updated_after_save_called(self):
        TestResource.caching = True
        res1 = TestResource(path=self.TEST_PATH1).save()
        res1.rating = 40
        res1.text = 'TEXT!'
        res1.save()
        self.assertEqual(TestResource.get(path=self.TEST_PATH1).rating, 40)
        self.assertEqual(TestResource.get(path=self.TEST_PATH1).text, 'TEXT!')

    def test_caching_on_set___values_updated_after_bulk_called(self):
        TestResource.caching = True
        res1 = TestResource(path=self.TEST_PATH1).save()
        res1.rating = 40
        res1.text = 'TEXT!'
        TestResource.bulk(update=[res1])
        self.assertEqual(TestResource.get(path=self.TEST_PATH1).rating, 40)
        self.assertEqual(TestResource.get(path=self.TEST_PATH1).text, 'TEXT!')

    def test_nested_resource_on_resource___endpoint_callable_as_a_method(self):
        tree1 = TestTreeResource(name='tree1', parent=TestTreeResource(name='tree2'))
        TestTreeResource(name='tree3', children=[tree1.parent])
        self.assertEqual(tree1.depth.get(), 2)

    def test_nested_resource_on_resource_with_args___endpoint_callable_as_a_method(self):
        self.assertEqual(TestTreeResource.add(1, 2).put(), 3)

    def test_nested_resource_on_resource_with_kwargs___endpoint_callable_as_a_method(self):
        self.assertEqual(TestTreeResource.mult.post(num1=3, num2=2), 6)

    def test_nested_resource_on_resource_with_too_few_args___throws_exception(self):
        self.assertRaises(ErrorResponse, TestTreeResource.add(1).put)

    def test_nested_resource_on_resource_with_too_many_args___throws_exception(self):
        self.assertRaises(ErrorResponse, TestTreeResource.add(1, 2, 3).put)

    def test_nested_resource_on_resource_with_too_few_kwargs___throws_exception(self):
        self.assertRaises(IncorrectNestedResourceKwargs, TestTreeResource.mult.post, num1=1)

    def test_nested_resource_on_resource_with__too_manykwargs___endpoint_callable_as_a_method(self):
        self.assertEqual(TestTreeResource.mult(num1=3, num2=2, num3=0).post(), 6)

    def test_nested_resource_returning_related_resource___resource_object_returned(self):
        CHILD_NAME = 'tree2'
        tree1 = TestTreeResource(name='tree1', children=[TestTreeResource(name=CHILD_NAME)])
        self.assertEqual(CHILD_NAME, tree1.chained.nested.child.get().name)

    def test_nested_resource_on_resource_with_too_few_args_in_get___more_explicit_exception_raised(self):
        tree1 = TestTreeResource(name='tree1', children=[])
        self.assertRaises(IncorrectNestedResourceArgs, tree1.chained.nested.child(1).get)

    def test_nested_resource_with_wrong_rest_method___exception_raised(self):
        tree1 = TestTreeResource(name='tree1', children=[])
        self.assertRaises(RestMethodNotAllowed, tree1.chained.nested.child(1).post)

    def test_nested_resource_with_resource_list___list_of_resources_returned(self):
        tree1 = TestTreeResource(name='tree1')
        tree2 = TestTreeResource(name='tree2')
        parent = TestTreeResource(name='parent', children=[tree1, tree2])
        self.assertEqual([tree1, tree2, parent], list(parent.nested_children().all()))

    def test_nested_resource_with_empty_resource_list___exception_raised(self):
        tree1 = TestTreeResource(name='tree1')
        tree2 = TestTreeResource(name='tree2')
        parent = TestTreeResource(name='parent', children=[tree1, tree2])
        self.assertRaises(NoResourcesExist, list, parent.nested_children().filter(name='fake'))

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

    def test_delete_on_all_resources___no_resources_returned_from_all(self):
        TestResource.bulk(create=[{'path': self.TEST_PATH1}, {'path': self.TEST_PATH2}])
        self.assertEqual(2, len(TestResource))
        TestResource.delete_all()
        self.assertEqual(0, len(TestResource))

    def test_delete_on_all_resources___resource_objects_marked_as_deleted(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        TestResource.delete_all()
        self.assertRaises(ResourceDeleted, res1.save)
        self.assertRaises(ResourceDeleted, res2.save)

    def test_dir_on_resource_instance___fields_returned_in_addition(self):
        tree1 = TestTreeResource(name='tree1')
        self.assertTrue('name' in dir(tree1))
        self.assertTrue('parent' in dir(tree1))
        self.assertTrue('children' in dir(tree1))

    def test_default_value_in_field___value_set_from_schema1(self):
        res1 = TestResource(path=self.TEST_PATH1)
        self.assertEqual(res1.rating, 50)

    def test_default_value_in_field___value_set_from_schema2(self):
        res1 = TestResource(path=self.TEST_PATH1)
        self.assertEqual(res1.date, None)

    def test_default_value_in_field___exception_raised_if_value_required(self):
        res1 = TestResource(rating=self.TEST_RATING1)
        self.assertRaises(NoDefaultValueInSchema, getattr, res1, 'path')

    def test_setting_value_before_saving___value_cached_to_save(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1)
        res1.rating = self.TEST_RATING1 + 1
        res1.save()
        res2 = TestResource.get(path=self.TEST_PATH1)
        self.assertEqual(res2.rating, self.TEST_RATING1 + 1)

    def test_resource_with_invalid_field_name___exception_raised(self):
        self.assertRaises(InvalidFieldName, FACTORY.invalid_field, limit=1)

    def test_resource_with_readonly_field___setting_field_raises_exception(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1)
        self.assertRaises(ReadOnlyField, setattr, res1, 'reviewed', True)

    def test_resource_with_not_nullable_field___setting_field_to_null_raises_exception(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1)
        self.assertRaises(FieldNotNullable, setattr, res1, 'rating', None)

    def test_misuse_of_resource_class___exceptions_raised(self):
        from tastytopping.resource import Resource
        self.assertRaises(NotImplementedError, Resource, path=self.TEST_PATH1)
        class NoNameResource(Resource):
            api_url = TestResource.api_url
        self.assertRaises(NotImplementedError, NoNameResource, path=self.TEST_PATH1)

    def test_copying_resources___shallow_copy_works(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        res2 = copy.copy(res1)
        self.assertEqual(res1, res2)

    def test_copying_resources___deep_copy_works(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        res1.set_caching(False)
        res2 = copy.deepcopy(res1)
        self.assertFalse(res2._caching)

    def test_string_representations___doesnt_crash(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        repr(res1)
        str(res1)
        repr(res1._schema())
        str(res1._schema())
        str(ReadOnlyField('text', 1))

    def test_help___doesnt_crash(self):
        FACTORY.test_resource.help()
        FACTORY.test_resource.help(verbose=True)

    def test_resource_with_malformed_uri___api_cannot_create_full_uri(self):
        res1 = FACTORY.test_resource(_fields='/something/that/wont/merge/')
        self.assertRaises(BadUri, getattr, res1, 'rating')

    # TODO Pickle
    #def test_pickling_resource___resource_useable(self):
    #    res1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
    #    res2 = pickle.loads(pickle.dumps(res1))
    #    res2.rating = 11
    #    res2.save()

    #def test_zzz(self):
    #    import sys
    #    sys.stderr.write('\n' + TestResource.help())
    #    sys.stderr.write('\n' + FACTORY.user.help())
    #    sys.stderr.write('\n' + TestTreeResource.help(verbose=True))
    #    sys.stderr.write('\n' + TestTreeResource.help())


    # FEATURES:
    # TODO Allow files to be passed when tastypie supports it (https://github.com/cboelsen/tastytopping/issues/1)
    # TODO Have a generate_docs() method on the factory.
    # TODO Have 'help' return RST?!?
    # TODO Single dispatch functions.
    # TODO asyncio

    # TESTING:
    # TODO Re-enable django-dev in py33-dev and py27-dev when tastypie works with django 1.7 again.
    # TODO Test cookies

    # DOCS
    # TODO Getting started
    # TODO Optimizations / Bulk
    # TODO Generating API help.
    # TODO Release notes.
    # TODO Cookbook
    # TODO Nested resources.


TestResource.auth = HttpApiKeyAuth(IntegrationTest.TEST_USERNAME, IntegrationTest.TEST_API_KEY)

CACHE = (
    TestResource(path='cache1'),
    TestResourceDerived(path='cache3'),
    TestTreeResource(name='cache4'),
)


if __name__ == "__main__":
    unittest.main()
