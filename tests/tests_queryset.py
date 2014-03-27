#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: skip-file


from datetime import datetime
import unittest

from tastytopping import *

from .tests_base import *


################################# TEST CLASS ##################################
class QuerySetTests(TestsBase):

    def test_indexing_resources___index_number_refers_to_item_number_in_list(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        self.assertEqual(self.TEST_PATH1 + '3', TestResource.all()[3].path)
        self.assertEqual(self.TEST_PATH1 + '7', TestResource.all()[7].path)

    def test_slicing_resources___slice_refers_to_item_numbers_in_list(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        resource_list = TestResource.all()[2:7]
        self.assertEqual(self.TEST_PATH1 + '4', resource_list[2].path)
        self.assertEqual(self.TEST_PATH1 + '6', resource_list[4].path)

    def test_multiple_filters___filters_are_combined(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'title': 'A'},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'title': 'B'},
            {'path': self.TEST_PATH1+'3', 'rating': 40, 'title': 'A'},
        ])
        self.assertEqual(
            TestResource.get(path=self.TEST_PATH1+'1'),
            TestResource.filter(title='A').all().filter(rating=20)[0]
        )

    def test_too_large_index___exception_raised(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        with self.assertRaises(IndexError):
            TestResource.all()[10]
        with self.assertRaises(IndexError):
            TestResource.all()[9:11]
        with self.assertRaises(IndexError):
            TestResource.all()[-10]
        with self.assertRaises(IndexError):
            TestResource.all()[-11:-9]

    def test_negative_index___correct_resource_returned(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        self.assertEqual(self.TEST_PATH1 + '8', TestResource.all()[-2].path)
        self.assertEqual(self.TEST_PATH1 + '5', TestResource.all()[3:-3][-2].path)
        self.assertEqual(self.TEST_PATH1 + '4', TestResource.all()[-8:8][2].path)
        self.assertEqual(self.TEST_PATH1 + '5', TestResource.all()[-6:-3][1].path)

    def test_wrong_index_type___exception_raised(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        with self.assertRaises(TypeError):
            TestResource.all()['a']

    def test_empty_slice___empty_list_returned(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        self.assertFalse(TestResource.all()[1:1])

    def test_queryset_to_bool_conversion___empty_list_returns_false(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        self.assertTrue(TestResource.filter(path=self.TEST_PATH1 + '1'))
        self.assertFalse(TestResource.filter(path=self.TEST_PATH1 + '21'))

    def test_queryset_stores_iterated_values___same_values_returned_on_next_loop1(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        all_resources = TestResource.all()
        self.assertEqual(list(all_resources), list(all_resources))

    def test_queryset_stores_iterated_values___same_values_returned_on_next_loop2(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        all_resources = TestResource.all()
        next(iter(all_resources))
        next(iter(all_resources))
        self.assertEqual(list(all_resources), list(all_resources))

    def test_multiple_order_by___ordering_is_combined(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 40, 'date': datetime(2014, 1, 1)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'date': datetime(2014, 1, 3)},
            {'path': self.TEST_PATH1+'3', 'rating': 20, 'date': datetime(2014, 1, 2)},
            {'path': self.TEST_PATH1+'9', 'rating': 60, 'date': datetime(2014, 1, 4)},
        ])
        resources = TestResource.filter(rating__lt=50).order_by('rating').order_by('-date')
        self.assertEquals(resources[0].path, self.TEST_PATH1+'2')
        self.assertEquals(resources[1].path, self.TEST_PATH1+'3')
        self.assertEquals(resources[2].path, self.TEST_PATH1+'1')

    def test_slicing_resources_with_step___stepping_works(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        resource_list = TestResource.all()[1:9:2]
        self.assertEqual(self.TEST_PATH1 + '1', resource_list[0].path)
        self.assertEqual(self.TEST_PATH1 + '3', resource_list[1].path)
        self.assertEqual(self.TEST_PATH1 + '5', resource_list[2].path)

    def test_slicing_resources_with_negative_step___order_reversed(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        resource_list = TestResource.all()[9:1:-2]
        self.assertEqual(self.TEST_PATH1 + '9', resource_list[0].path)
        self.assertEqual(self.TEST_PATH1 + '7', resource_list[1].path)
        self.assertEqual(self.TEST_PATH1 + '3', resource_list[-1].path)

    def test_negative_index_with_negative_slicing___correct_resource_returned(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i)} for i in range(0, 10)])
        self.assertEqual(self.TEST_PATH1 + '5', TestResource.all()[-3:3:-2][-1].path)
        self.assertEqual(self.TEST_PATH1 + '5', TestResource.all()[8:-8:-3][1].path)
        self.assertEqual(self.TEST_PATH1 + '6', TestResource.all()[-3:-6:-1][1].path)

    def test_delete_on_queryset___only_filtered_resources_deleted(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        TestResource.filter(rating__gt=5).delete()
        self.assertEquals(6, TestResource.all().count())
        self.assertEquals(5, TestResource.all()[-1].rating)

    def test_delete_on_queryset___delete_list_resource_when_no_filters(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        TestResource.all().delete()
        self.assertEquals(0, TestResource.all().count())

    def test_reverse_queryset___returned_resources_order_reversed_list(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        normal_order = TestResource.all().order_by('rating')
        reverse_order = normal_order.reverse()
        self.assertEqual(list(normal_order)[0], list(reverse_order)[-1])
        self.assertEqual(list(normal_order)[-1], list(reverse_order)[0])

    def test_reverse_queryset___returned_resources_order_reversed_slice(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        normal_order = TestResource.all().order_by('rating')
        reverse_order = normal_order.reverse()
        self.assertEqual(normal_order[:][0], reverse_order[:][-1])
        self.assertEqual(normal_order[:][-1], reverse_order[:][0])

    def test_reverse_twice_queryset___returned_resources_order_not_reversed(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        normal_order = TestResource.all()
        reverse_order = normal_order.reverse().reverse()
        self.assertEqual(normal_order[:][0], reverse_order[:][0])
        self.assertEqual(normal_order[:][-1], reverse_order[:][-1])

    def test_reverse_queryset_iterator___returned_resources_order_reversed_list(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        normal_order = TestResource.all().order_by('rating')
        reverse_order = normal_order.reverse()
        self.assertEqual(list(normal_order.iterator())[0], list(reverse_order.iterator())[-1])
        self.assertEqual(list(normal_order)[-1], list(reverse_order.iterator())[0])

    def test_reverse_without_order___exception_raised(self):
        with self.assertRaises(OrderByRequiredForReverse):
            TestResource.all().reverse()[0]

    def test_queryset_exist___states_whether_resources_match_query(self):
        self.assertFalse(TestResource.all().exists())
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        self.assertTrue(bool(TestResource.all()))
        self.assertFalse(bool(TestResource.filter(rating__gt=20)))
        self.assertTrue(TestResource.filter(rating__lt=5).exists())

    def test_latest_resource_by_date___returns_the_correct_resource(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'date': datetime(2014, 1, 1)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'date': datetime(2014, 1, 4)},
            {'path': self.TEST_PATH1+'3', 'rating': 20, 'date': datetime(2014, 1, 2)},
            {'path': self.TEST_PATH1+'4', 'rating': 60, 'date': datetime(2014, 1, 4)},
        ])
        resource = TestResource.filter(rating__lt=50).latest('date')
        self.assertEquals(resource.path, self.TEST_PATH1+'2')

    def test_latest_resource_by_date___previous_order_by_taken_into_account(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'date': datetime(2014, 1, 1)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'date': datetime(2014, 1, 4)},
            {'path': self.TEST_PATH1+'3', 'rating': 20, 'date': datetime(2014, 1, 2)},
            {'path': self.TEST_PATH1+'4', 'rating': 60, 'date': datetime(2014, 1, 4)},
        ])
        resource = TestResource.all().order_by('-rating').latest('date')
        self.assertEquals(resource.path, self.TEST_PATH1+'4')

    def test_earliest_resource_by_date___returns_the_correct_resource(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'date': datetime(2014, 1, 1)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'date': datetime(2014, 1, 4)},
            {'path': self.TEST_PATH1+'3', 'rating': 20, 'date': datetime(2014, 1, 2)},
            {'path': self.TEST_PATH1+'4', 'rating': 60, 'date': datetime(2014, 1, 4)},
        ])
        resource = TestResource.all().earliest('date')
        self.assertEquals(resource.path, self.TEST_PATH1+'1')

    def test_bulk_updates_on_full_queryset___all_resources_updated(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        TestResource.all().update(rating=60)
        all_resources = list(TestResource.all())
        self.assertEquals(60, all_resources[0].rating)
        self.assertEquals(60, all_resources[5].rating)
        self.assertEquals(60, all_resources[9].rating)

    def test_bulk_updates_on_filtered_queryset___all_resources_matching_query_updated(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'text': 'A', 'date': datetime(2013, 3, 1)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'text': 'B', 'date': datetime(2013, 3, 2)},
            {'path': self.TEST_PATH1+'3', 'rating': 20, 'text': 'C', 'date': datetime(2013, 3, 3)},
            {'path': self.TEST_PATH1+'4', 'rating': 60, 'text': 'D', 'date': datetime(2013, 3, 4)},
        ])
        NEW_DATE = datetime(2013, 3, 5)
        TestResource.filter(rating=20).update(date=NEW_DATE)
        all_resources = list(TestResource.all())
        self.assertEquals(NEW_DATE, all_resources[0].date)
        self.assertEquals('A', all_resources[0].text)
        self.assertEquals(NEW_DATE, all_resources[2].date)
        self.assertEquals('C', all_resources[2].text)
        self.assertEquals(datetime(2013, 3, 4), all_resources[3].date)
        self.assertEquals('D', all_resources[3].text)

    def test_queryset_iterator___evaluates_results_each_time(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        all_resources = TestResource.all()
        self.assertEqual(10, len(list(all_resources.iterator())))
        TestResource(path=self.TEST_PATH1).save()
        self.assertEqual(11, len(list(all_resources.iterator())))

    def test_queryset_first_last___returns_the_first_resource(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        self.assertEqual(self.TEST_PATH1 + '0', TestResource.all().first().path)
        self.assertEqual(None, TestResource.filter(rating=50).first())
        self.assertEqual(self.TEST_PATH1 + '9', TestResource.all().last().path)
        self.assertEqual(None, TestResource.filter(rating=50).last())

    def test_empty_queryset___returns_empty_list(self):
        empty = TestResource.none()
        with self.assertRaises(IndexError):
            empty.none()[0]
        # TODO Is this the behaviour I want?!?!
        with self.assertRaises(NoResourcesExist):
            list(empty)
        self.assertEqual(0, empty.count())
        self.assertEqual([], list(empty.iterator()))
        self.assertRaises(NoResourcesExist, empty.earliest, 'date')
        self.assertRaises(NoResourcesExist, empty.all().latest, 'date')
        empty.update(rating=0)
        empty.delete()
        self.assertRaises(NoResourcesExist, TestResource.all().latest, 'date')

    def test_abstract_querysets_abstractness___exceptions_raised(self):
        abstract = queryset._AbstractQuerySet(TestResource)
        self.assertRaises(NotImplementedError, abstract._queryset_class)
        self.assertRaises(NotImplementedError, abstract.update)
        self.assertRaises(NotImplementedError, abstract.delete)
        self.assertRaises(NotImplementedError, abstract.count)
        self.assertRaises(NotImplementedError, abstract.iterator)
        self.assertRaises(NotImplementedError, abstract.latest, 'date')
        self.assertRaises(NotImplementedError, abstract.earliest, 'date')
        with self.assertRaises(NotImplementedError):
            abstract & abstract

    def test_logical_and_with_empty_queryset___empty_queryset_returned(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        combined1 = TestResource.all() & TestResource.none()
        combined2 = TestResource.none() & TestResource.all()
        self.assertEqual(0, combined1.count())
        self.assertEqual(0, combined2.count())

    def test_logical_and_with_different_filters___combined_queryset_returned(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'text': 'A', 'date': datetime(2013, 3, 1)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'text': 'B', 'date': datetime(2013, 3, 2)},
            {'path': self.TEST_PATH1+'3', 'rating': 20, 'text': 'C', 'date': datetime(2013, 3, 3)},
            {'path': self.TEST_PATH1+'4', 'rating': 60, 'text': 'D', 'date': datetime(2013, 3, 4)},
        ])
        combined = TestResource.filter(rating=20) & TestResource.filter(date=datetime(2013, 3, 2))
        self.assertEqual(self.TEST_PATH1+'2', combined.get().path)

    def test_logical_and_with_same_fields_different_filters___combined_queryset_returned(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'text': 'A', 'date': datetime(2013, 3, 1)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'text': 'B', 'date': datetime(2013, 3, 2)},
            {'path': self.TEST_PATH1+'3', 'rating': 80, 'text': 'C', 'date': datetime(2013, 3, 3)},
            {'path': self.TEST_PATH1+'4', 'rating': 60, 'text': 'D', 'date': datetime(2013, 3, 4)},
        ])
        combined = TestResource.filter(rating__gt=30) & TestResource.filter(rating__lt=70)
        self.assertEqual(self.TEST_PATH1+'4', combined.get().path)

    def test_logical_and_with_same_filters___filters_appended(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'text': 'A', 'date': datetime(2013, 3, 1)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'text': 'B', 'date': datetime(2013, 3, 2)},
            {'path': self.TEST_PATH1+'3', 'rating': 80, 'text': 'C', 'date': datetime(2013, 3, 3)},
            {'path': self.TEST_PATH1+'4', 'rating': 60, 'text': 'D', 'date': datetime(2013, 3, 4)},
        ])
        combined = TestResource.filter(rating__in=[20, 30]) & TestResource.filter(rating__in=[20, 80])
        self.assertEqual(2, combined.count())

    def test_logical_and_with_order_by___ordering_combined(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'text': 'A', 'date': datetime(2013, 3, 1)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'text': 'B', 'date': datetime(2013, 3, 3)},
            {'path': self.TEST_PATH1+'3', 'rating': 20, 'text': 'C', 'date': datetime(2013, 3, 2)},
            {'path': self.TEST_PATH1+'4', 'rating': 60, 'text': 'D', 'date': datetime(2013, 3, 1)},
        ])
        combined = TestResource.all().order_by('rating') & TestResource.all().order_by('date')
        self.assertEqual(self.TEST_PATH1+'3', combined[1].path)

    def test_logical_and_multiple_times___combination_correct(self):
        TestResource.create([
            {'path': self.TEST_PATH1+'1', 'rating': 20, 'date': datetime(2013, 3, 2)},
            {'path': self.TEST_PATH1+'2', 'rating': 20, 'date': datetime(2013, 3, 3)},
            {'path': self.TEST_PATH1+'3', 'rating': 30, 'date': datetime(2013, 3, 3)},
            {'path': self.TEST_PATH1+'4', 'rating': 40, 'date': datetime(2013, 3, 3)},
        ])
        combined = TestResource.filter(rating__in=[20, 30]) & TestResource.filter(rating__in=[20, 40]) & TestResource.filter(date=datetime(2013, 3, 3))
        self.assertEqual(self.TEST_PATH1+'2', combined.get().path)

    def test_logical_and_with_queryset_of_different_resource___exception_raised(self):
        with self.assertRaises(TypeError):
            TestResource.all() & FACTORY.container.all()

    def test_logical_and_with_wrong_type___exception_raised(self):
        with self.assertRaises(TypeError):
            TestResource.all() & 5

    def test_using_previously_cached_values_in_slicing___correct_results_returned(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        all_resources = TestResource.all()
        for i, _ in enumerate(all_resources):
            if i > 6:
                break
        self.assertEqual(2, all_resources[2].rating)
        self.assertEqual(3, all_resources[2:5][-2].rating)
        self.assertEqual(9, all_resources[6:][-1].rating)

    def test_prefetch_related_on_non_related_field___has_no_effect(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 10)])
        all_resources = TestResource.all().prefetch_related('rating')
        self.assertEqual(2, all_resources[2].rating)

    def test_prefetch_related___full_related_field_stored_on_return_of_iter(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 50)])
        FACTORY.container.create([
            {'test': TestResource.get(path=self.TEST_PATH1+'11')},
            {'test': TestResource.get(path=self.TEST_PATH1+'12')},
            {'test': TestResource.get(path=self.TEST_PATH1+'13')},
        ])
        all_containers = FACTORY.container.all().prefetch_related('test')
        self.assertEqual(11, list(all_containers)[0].test.rating)
        self.assertEqual(12, list(all_containers)[1].test.rating)
        self.assertEqual(13, list(all_containers)[2].test.rating)

    def test_prefetch_related___full_related_field_stored_on_return_of_slice(self):
        TestResource.create([{'path': self.TEST_PATH1 + str(i), 'rating': i} for i in range(0, 50)])
        FACTORY.container.create([
            {'test': TestResource.get(path=self.TEST_PATH1+'11')},
            {'test': TestResource.get(path=self.TEST_PATH1+'12')},
            {'test': TestResource.get(path=self.TEST_PATH1+'13')},
        ])
        all_containers = FACTORY.container.all().prefetch_related('test')
        self.assertEqual(11, all_containers[0].test.rating)
        self.assertEqual(12, all_containers[1].test.rating)
        self.assertEqual(13, all_containers[2].test.rating)

    def test_prefetch_related_with_to_many_field___full_related_fields_stored_on_return_of_iter(self):
        FACTORY.tree.create([{'name': str(i)} for i in range(20)])
        roots = [FACTORY.tree.get(name='0'), FACTORY.tree.get(name='1')]
        FACTORY.tree.create([
            {'name': '100', 'parent': roots[0]},
            {'name': '101', 'parent': roots[0]},
            {'name': '102', 'parent': roots[0]},
            {'name': '103', 'parent': roots[1]},
            {'name': '104', 'parent': roots[1]},
        ])
        all_trees = list(FACTORY.tree.all().prefetch_related('children', 'parent'))
        self.assertEqual('100', all_trees[0].children[0].name)
        self.assertEqual('101', all_trees[0].children[1].name)
        self.assertEqual('103', all_trees[1].children[0].name)
        self.assertEqual('0', all_trees[21].parent.name)
