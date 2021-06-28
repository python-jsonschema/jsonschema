from unittest import TestCase

from jsonschema._utils import dict_equal, list_equal


class TestDictEqual(TestCase):

    def test_equal_dictionaries(self):
        dict_1 = {"a": "b", "c": "d"}
        dict_2 = {"c": "d", "a": "b"}
        self.assertTrue(dict_equal(dict_1, dict_2))

    def test_missing_key(self):
        dict_1 = {"a": "b", "c": "d"}
        dict_2 = {"c": "d", "x": "b"}
        self.assertFalse(dict_equal(dict_1, dict_2))

    def test_additional_key(self):
        dict_1 = {"a": "b", "c": "d"}
        dict_2 = {"c": "d", "a": "b", "x": "x"}
        self.assertFalse(dict_equal(dict_1, dict_2))

    def test_missing_value(self):
        dict_1 = {"a": "b", "c": "d"}
        dict_2 = {"c": "d", "a": "x"}
        self.assertFalse(dict_equal(dict_1, dict_2))

    def test_empty_dictionaries(self):
        dict_1 = {}
        dict_2 = {}
        self.assertTrue(dict_equal(dict_1, dict_2))

    def test_one_none(self):
        dict_1 = None
        dict_2 = {"a": "b", "c": "d"}
        with self.assertRaises(AttributeError):
            self.assertFalse(dict_equal(dict_1, dict_2))
        with self.assertRaises(AttributeError):
            self.assertFalse(dict_equal(dict_1, dict_2))

    def test_both_none(self):
        with self.assertRaises(AttributeError):
            self.assertFalse(dict_equal(None, None))

    def test_same_item(self):
        dict_1 = {"a": "b", "c": "d"}
        self.assertTrue(dict_equal(dict_1, dict_1))

    def test_nested_dict_equal(self):
        dict_1 = {"a": {"a": "b", "c": "d"}, "c": "d"}
        dict_2 = {"c": "d", "a": {"a": "b", "c": "d"}}
        self.assertTrue(dict_equal(dict_1, dict_2))

    def test_nested_dict_unequal(self):
        dict_1 = {"a": {"a": "b", "c": "d"}, "c": "d"}
        dict_2 = {"c": "d", "a": {"a": "b", "c": "x"}}
        self.assertFalse(dict_equal(dict_1, dict_2))

    def test_nested_list_equal(self):
        dict_1 = {"a": ["a", "b", "c", "d"], "c": "d"}
        dict_2 = {"c": "d", "a": ["a", "b", "c", "d"]}
        self.assertTrue(dict_equal(dict_1, dict_2))

    def test_nested_list_unequal(self):
        dict_1 = {"a": ["a", "b", "c", "d"], "c": "d"}
        dict_2 = {"c": "d", "a": ["b", "c", "d", "a"]}
        self.assertFalse(dict_equal(dict_1, dict_2))


class TestListEqual(TestCase):

    def test_equal_lists(self):
        list_1 = ["a", "b", "c"]
        list_2 = ["a", "b", "c"]
        self.assertTrue(list_equal(list_1, list_2))

    def test_unsorted_lists(self):
        list_1 = ["a", "b", "c"]
        list_2 = ["b", "b", "a"]
        self.assertFalse(list_equal(list_1, list_2))

    def test_first_list_larger(self):
        list_1 = ["a", "b", "c"]
        list_2 = ["a", "b"]
        self.assertFalse(list_equal(list_1, list_2))

    def test_second_list_larger(self):
        list_1 = ["a", "b"]
        list_2 = ["a", "b", "c"]
        self.assertFalse(list_equal(list_1, list_2))

    def test_list_with_none_unequal(self):
        list_1 = ["a", "b", None]
        list_2 = ["a", "b", "c"]
        self.assertFalse(list_equal(list_1, list_2))

        list_1 = ["a", "b", None]
        list_2 = [None, "b", "c"]
        self.assertFalse(list_equal(list_1, list_2))

    def test_list_with_none_equal(self):
        list_1 = ["a", None, "c"]
        list_2 = ["a", None, "c"]
        self.assertTrue(list_equal(list_1, list_2))

    def test_empty_list(self):
        list_1 = []
        list_2 = []
        self.assertTrue(list_equal(list_1, list_2))

    def test_one_none(self):
        list_1 = None
        list_2 = []
        with self.assertRaises(TypeError):
            self.assertTrue(list_equal(list_1, list_2))

    def test_both_none(self):
        list_1 = None
        list_2 = None
        with self.assertRaises(TypeError):
            self.assertTrue(list_equal(list_1, list_2))

    def test_same_list(self):
        list_1 = ["a", "b", "c"]
        self.assertTrue(list_equal(list_1, list_1))

    def test_equal_nested_lists(self):
        list_1 = ["a", ["b", "c"], "d"]
        list_2 = ["a", ["b", "c"], "d"]
        self.assertTrue(list_equal(list_1, list_2))

    def test_unequal_nested_lists(self):
        list_1 = ["a", ["b", "c"], "d"]
        list_2 = ["a", [], "c"]
        self.assertFalse(list_equal(list_1, list_2))
