#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: skip-file


from tastytopping import *

from .tests_base import *


################################# TEST CLASS ##################################
class NestedTests(TestsBase):

    def test_nested_resource_on_resource___endpoint_callable_as_a_method(self):
        tree1 = TestTreeResource(name='tree1', parent=TestTreeResource(name='tree2').save()).save()
        TestTreeResource(name='tree3', children=[tree1.parent]).save()
        self.assertEqual(tree1.nested.depth.get(), 2)

    def test_nested_resource_on_resource_with_args___endpoint_callable_as_a_method(self):
        self.assertEqual(TestTreeResource.nested.add(1, 2).put(), 3)

    def test_nested_resource_on_resource_with_kwargs___endpoint_callable_as_a_method(self):
        self.assertEqual(TestTreeResource.nested.mult.post(num1=3, num2=2), 6)

    def test_nested_resource_on_resource_with_too_few_args___throws_exception(self):
        self.assertRaises(ErrorResponse, TestTreeResource.nested.add(1).put)

    def test_nested_resource_on_resource_with_too_many_args___throws_exception(self):
        self.assertRaises(ErrorResponse, TestTreeResource.nested.add(1, 2, 3).put)

    def test_nested_resource_on_resource_with_too_few_kwargs___throws_exception(self):
        self.assertRaises(IncorrectNestedResourceKwargs, TestTreeResource.nested.mult.post, num1=1)

    def test_nested_resource_on_resource_with__too_manykwargs___endpoint_callable_as_a_method(self):
        self.assertEqual(TestTreeResource.nested.mult(num1=3, num2=2, num3=0).post(), 6)

    def test_nested_resource_returning_related_resource___resource_object_returned(self):
        CHILD_NAME = 'tree2'
        tree1 = TestTreeResource(name='tree1', children=[TestTreeResource(name=CHILD_NAME).save()]).save()
        self.assertEqual(CHILD_NAME, tree1.nested.chained.nested.child.get().name)

    def test_nested_resource_returning_related_resource_dictionary___resource_object_returned(self):
        CHILD_NAME = 'tree2'
        tree1 = TestTreeResource(name='tree1', children=[TestTreeResource(name=CHILD_NAME).save()]).save()
        self.assertEqual(CHILD_NAME, tree1.nested.chained.nested.child_dict.get().name)

    def test_nested_resource_on_resource_with_too_few_args_in_get___more_explicit_exception_raised(self):
        tree1 = TestTreeResource(name='tree1', children=[]).save()
        self.assertRaises(IncorrectNestedResourceArgs, tree1.nested.chained.nested.child(1).get)

    def test_nested_resource_with_wrong_rest_method___exception_raised(self):
        tree1 = TestTreeResource(name='tree1', children=[]).save()
        self.assertRaises(RestMethodNotAllowed, tree1.nested.chained.nested.child(1).post)

    def test_nested_resource_with_resource_list___list_of_resources_returned(self):
        tree1 = TestTreeResource(name='tree1').save()
        tree2 = TestTreeResource(name='tree2').save()
        parent = TestTreeResource(name='parent', children=[tree1, tree2]).save()
        self.assertEqual([tree1, tree2, parent], list(parent.nested.nested_children().get()))

    def test_nested_resource_with_empty_resource_list___empty_list_returned(self):
        tree1 = TestTreeResource(name='tree1').save()
        tree2 = TestTreeResource(name='tree2').save()
        parent = TestTreeResource(name='parent', children=[tree1, tree2]).save()
        self.assertEqual([], parent.nested.nested_children(name='fake').get())
