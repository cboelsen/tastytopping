#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: skip-file


import copy
from datetime import datetime
import pickle
import unittest

from tastytopping import *

from .tests_base import *

# Import the other tests to run.
from .tests_auth import AuthTests
from .tests_queryset import QuerySetTests
from .tests_nested import NestedTests


################################# TEST CLASS ##################################
class IntegrationTests(TestsBase):

    def test_create___object_returned_with_same_fields(self):
        resource = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        self.assertEqual(resource.path, self.TEST_PATH1)
        self.assertEqual(resource.rating, self.TEST_RATING1)

    def test_create_with_factory___object_returned_with_same_fields(self):
        factory = ResourceFactory('http://localhost:8111/test/api/v1')
        factory.test_resource.auth = HTTPApiKeyAuth(self.TEST_USERNAME, self.TEST_API_KEY)
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

    def test_call_save_when_no_changes___no_op(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource1.save()

    def test_get_non_existent_field_on_object___raises_exception(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1)
        with self.assertRaises(AttributeError):
            resource1.fake_field

    def test_get_non_existent_field_on_class___raises_exception(self):
        with self.assertRaises(AttributeError):
            TestResource.fake_field

    def test_delete_object___no_object_to_get(self):
        resource = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        resource.delete()
        self.assertEqual(0, TestResource.filter(path=self.TEST_PATH1).count())

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
        resource1.date = datetime(2013, 12, 6)
        resource1.save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        self.assertEqual(resource1.date, resource2.date)

    def test_datetime_objects_with_ms___streams_both_ways(self):
        resource1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1)
        resource1.date = datetime(2013, 12, 6, 1, 1, 1, 500)
        resource1.save()
        resource2 = TestResource.get(path=self.TEST_PATH1)
        self.assertEqual(resource1.date, resource2.date)

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

    def test_bad_address___exception_raised(self):
        with self.assertRaises(CannotConnectToAddress):
            factory = ResourceFactory('http://localhost:8888/test/api/v1')

    def test_bad_resource___exception_raised(self):
        with self.assertRaises(AttributeError):
            FACTORY.not_exist

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
        TestResource.create(resources)
        resources = TestResource.all()
        self.assertEqual(len(set(resources)), NUM_RESOURCES)

    def test_more_resources_to_get_than_given_limit___api_only_retrieve_up_to_limit(self):
        NUM_RESOURCES = 8
        LIMIT = 5
        resources = [{'path': self.TEST_PATH1 + str(i), 'rating': self.TEST_RATING1} for i in range(NUM_RESOURCES)]
        TestResource.create(resources)
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
        self.assertRaises(RestMethodNotAllowed, FACTORY.user(username='bob').save)

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
        tree1 = TestTreeResource(name='tree1').save()
        tree2 = TestTreeResource(name='tree2').save()
        parent = TestTreeResource(name='parent', children=[tree1, tree2]).save()
        self.assertEqual(TestTreeResource.get(name='parent').children, [tree1, tree2])

    def test_update_resource_with_multiple_resources_in_related_field___multiple_resources_accepted(self):
        parent1 = TestTreeResource(name='parent1').save()
        parent2 = TestTreeResource(name='parent2').save()
        tree1 = TestTreeResource(name='tree1').save()
        tree2 = TestTreeResource(name='tree2').save()
        parent1.children = [tree1]
        parent1.children += [tree2]
        parent1.save()
        self.assertEqual(TestTreeResource.get(children=parent1.children).children, [tree1, tree2])

    def test_create_resource_with_same_parent_multiple_times___multiple_resources_returned_in_parent(self):
        root = TestTreeResource(name='root').save()
        tree1 = TestTreeResource(name='tree1', parent=root).save()
        tree2 = TestTreeResource(name='tree2')
        tree2.parent = root
        tree2.save()
        root.refresh()
        self.assertEqual(root.children, [tree1, tree2])

    def test_create_resource_with_explicitly_no_children___empty_list_accepted(self):
        root = TestTreeResource(name='root').save()
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
        self.assertEqual(TestResource.all().count(), 3)

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
        TestResource.create([{'path': self.TEST_PATH1}, {'path': self.TEST_PATH2}])
        res1 = TestResource.get(path=self.TEST_PATH1)
        res2 = TestResource.get(path=self.TEST_PATH2)

    def test_bulk_delete___multiple_resources_deleted(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        TestResource.bulk(delete=[res1, res2])
        self.assertEqual(0, TestResource.all().count())
        self.assertRaises(ResourceDeleted, setattr, res1, 'rating', 50)

    def test_get_with_no_results___throws_exception(self):
        self.assertRaises(NoResourcesExist, TestResource.get)

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

    def test_delete_on_all_resources___no_resources_returned_from_all(self):
        TestResource.create([{'path': self.TEST_PATH1}, {'path': self.TEST_PATH2}])
        self.assertEqual(2, len(TestResource))
        TestResource.all().delete()
        self.assertEqual(0, len(TestResource))

    def test_delete_on_all_resources___resource_objects_marked_as_deleted(self):
        res1 = TestResource(path=self.TEST_PATH1).save()
        res2 = TestResource(path=self.TEST_PATH2).save()
        TestResource.all().delete()
        self.assertRaises(ResourceDeleted, res1.save)
        self.assertRaises(ResourceDeleted, res2.save)

    def test_dir_on_resource_instance___fields_returned_in_addition(self):
        tree1 = TestTreeResource(name='tree1').save()
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
        res2 = copy.deepcopy(res1)
        self.assertEqual(res1, res2)

    def test_string_representations___doesnt_crash(self):
        res1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        repr(res1)
        str(res1)
        repr(res1._schema())
        str(res1._schema())
        str(ReadOnlyField('text', 1))

    def test_resource_with_malformed_uri___api_cannot_create_full_uri(self):
        res1 = FACTORY.test_resource(_fields='/something/that/wont/merge/')
        self.assertRaises(BadUri, getattr, res1, 'rating')

    def test_creating_two_identical_resources___second_is_unable_to_get_created_resource(self):
        res1 = FACTORY.no_unique(name='name', num=0).save()
        res2 = FACTORY.no_unique(name='name', num=0)
        self.assertRaises(MultipleResourcesReturned, res2.save)

    def test_creating_resource_disallowing_gets___created_resource_not_found_raised(self):
        self.assertRaises(CreatedResourceNotFound, FACTORY.only_post(path=self.TEST_PATH1).save)

    def test_date_only_model_field___correctly_handle_date_only(self):
        DATE = datetime(2014, 11, 12, 13, 14, 15)
        res1 = TestResource(path=self.TEST_PATH1, date_only=DATE).save()
        self.assertEqual(datetime(2014, 11, 12, 0, 0, 0), res1.date_only)

    def test_pickling_resource___resource_useable(self):
        root = TestTreeResource(name='root').save()
        tree1 = TestTreeResource(name='tree1').save()
        tree2 = TestTreeResource(name='tree2').save()
        parent = TestTreeResource(name='parent', children=[tree1, tree2]).save()
        parent2 = pickle.loads(pickle.dumps(parent))
        parent2.name = 'new_parent'
        parent2.parent = root.uri()
        parent2.save()

    def test_auth_kept_after_pickling___access_allowed(self):
        DATE_COMPARE = datetime.now()
        res1 = TestResource(path=self.TEST_PATH1, rating=self.TEST_RATING1).save()
        res1_copy = pickle.loads(pickle.dumps(res1))
        res1_copy.date = DATE_COMPARE
        res1_copy.save()
        res1.refresh()
        self.assertEqual(DATE_COMPARE, res1.date)

    def test_set_verify_false___continues_working(self):
        factory = ResourceFactory('http://localhost:8111/test/api/v1/', verify=False)
        self.assertFalse(factory.tree.verify)
        self.assertFalse(factory.tree._api().verify)
        factory.tree.all().count()

    def test_bad_uri_exception_takes_unicode_values___doesnt_raise_unicode_error(self):
        text = u'/some/name/Boßeln'
        list(TestResource.filter(path__startswith=text))

    def test_adding_nested_resource_from_another_api___nested_resources_retrieved_from_associated_factory(self):
        factory = ResourceFactory('http://localhost:8111/test/api/v2')
        factory.test_resource.auth = HTTPApiKeyAuth(TestsBase.TEST_USERNAME, TestsBase.TEST_API_KEY)
        factory.add_factory_dependency(FACTORY)
        user = FACTORY.user.get(username=self.TEST_USERNAME)
        factory.test_resource(path=self.TEST_PATH1, created_by=user).save()

        self.assertEqual(factory.test_resource.get(path=self.TEST_PATH1).created_by, user)

    # FEATURES:
    # TODO Don't raise ResourceDeleted when unable to connect to API.
    # TODO Don't update field if value the same.
    # TODO Only GET a new Resource when fields needed?!?! Should the exceptions be delayed?!? Will it be confusing?!?
    # TODO Allow files to be passed when tastypie supports it (https://github.com/cboelsen/tastytopping/issues/1)
    # TODO Allow 'exclude()' when tastypie allows it.
    # TODO Single dispatch functions in field?

    # TESTING:
    # TODO Re-enable django-dev in *-dev when tastypie works with django 1.8 again.

    # DOCS
    # TODO Pickling querysets


if __name__ == "__main__":
    unittest.main()
