#!/usr/bin/env python

# Project Byzantium: http://wiki.hacdc.org/index.php/Byzantium
# License: GPLv3

# state_test.py

from flexmock import flexmock  # http://has207.github.com/flexmock
import re
import state
import sqlite3
import unittest


class Simple(object):
    
    def __init__(self):
        self.attr1 = 'it is text'
        self.attr2 = 3


class DBBackedStateTest(unittest.TestCase):

    def setUp(self):
        self.connection = flexmock()
        flexmock(sqlite3).should_receive('connect').and_return(self.connection)
        self.state = state.DBBackedState('/no/real/path')
    
    def test_create_initialization_fragment_from_prototype(self):
        daemon = {'attr1': 'it is text', 'attr2': 3}
        result_str, result_vals = self.state._create_initialization_fragment_from_prototype(daemon)
        expected_str = '%s TEXT, %s NUMERIC'
        expected_vals = ('attr1', 'attr2')
        self.assertEqual(expected_str, result_str)
        self.assertEqual(expected_vals, result_vals)
        
    def test_create_query_fragment_from_item(self):
        daemon = {'attr1': 'it is text', 'attr2': 3}
        result_str, result_vals = self.state._create_query_fragment_from_item(daemon)
        expected_str = '?,?'
        expected_vals = ('it is text', 3)
        self.assertEqual(expected_str, result_str)
        self.assertEqual(expected_vals, result_vals)
        
    def test_create_update_query_fragment_from_item(self):
        daemon = {'attr1': 'it is text', 'attr2': 3}
        result_str, result_vals = self.state._create_update_query_fragment_from_item(daemon)
        # Can't count on any particular implementation spitting out the same order, so...
        self.assertEqual(1, len(re.findall('AND', result_str)))
        for attr in ['attr1=?', 'attr2=?']:
            self.assertTrue(attr in result_str)
        expected_vals = ('it is text', 3)
        self.assertEqual(sorted(expected_vals), sorted(result_vals))
        
    def test_create_update_setting_fragment_from_item(self):
        daemon = {'attr1': 'it is text', 'attr2': 3}
        result_str, result_vals = self.state._create_update_setting_fragment_from_item(daemon)
        # Can't count on any particular implementation spitting out the same order, so...
        self.assertEqual(1, len(re.findall(',', result_str)))
        for attr in ['attr1=?', 'attr2=?']:
            self.assertTrue(attr in result_str)
        expected_vals = ('it is text', 3)
        self.assertEqual(sorted(expected_vals), sorted(result_vals))


if __name__ == '__main__':
    unittest.main()