#!/usr/bin/env python

# Project Byzantium: http://wiki.hacdc.org/index.php/Byzantium
# License: GPLv3

# state_test.py

from flexmock import flexmock  # http://has207.github.com/flexmock
import re
import state
import sqlite3
import unittest


class DBBackedStateTest(unittest.TestCase):

    def setUp(self):
        self.connection = flexmock()
        flexmock(sqlite3).should_receive('connect').and_return(self.connection)
        self.state = state.DBBackedState('/no/real/path')
    
    def test_create_initialization_fragment_from_prototype(self):
        daemon = state.Daemon('', '', 0, '', '')
        result_str, result_vals = self.state._create_initialization_fragment_from_prototype(daemon)
        expected_str = '%s TEXT, %s TEXT, %s NUMERIC, %s TEXT, %s TEXT'
        expected_vals = ('initscript', 'name', 'port', 'showtouser', 'status')
        self.assertEqual(expected_str, result_str)
        self.assertEqual(expected_vals, result_vals)
        
    def test_create_query_fragment_from_item(self):
        daemon = state.Daemon('', '', 0, '', '')
        result_str, result_vals = self.state._create_query_fragment_from_item(daemon)
        expected_str = '?,?,?,?,?'
        expected_vals = ('', '', 0, '', '')
        self.assertEqual(expected_str, result_str)
        self.assertEqual(expected_vals, result_vals)
        
    def test_create_update_query_fragment_from_item(self):
        daemon = state.Daemon('', '', 0, '', '')
        result_str, result_vals = self.state._create_update_query_fragment_from_item(daemon)
        # Can't count on any particular implementation spitting out the same order, so...
        self.assertEqual(4, len(re.findall('AND', result_str)))
        for attr in ['initscript=?', 'name=?', 'port=?', 'showtouser=?', 'status=?']:
            self.assertTrue(attr in result_str)
        expected_vals = ('', '', 0, '', '')
        self.assertEqual(sorted(expected_vals), sorted(result_vals))
        
    def test_create_update_setting_fragment_from_item(self):
        daemon = state.Daemon('', '', 0, '', '')
        result_str, result_vals = self.state._create_update_setting_fragment_from_item(daemon)
        # Can't count on any particular implementation spitting out the same order, so...
        self.assertEqual(4, len(re.findall(',', result_str)))
        for attr in ['initscript=?', 'name=?', 'port=?', 'showtouser=?', 'status=?']:
            self.assertTrue(attr in result_str)
        expected_vals = ('', '', 0, '', '')
        self.assertEqual(sorted(expected_vals), sorted(result_vals))
        
        
if __name__ == '__main__':
    unittest.main()