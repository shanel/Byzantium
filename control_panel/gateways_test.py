#!/usr/bin/env python

# Project Byzantium: http://wiki.hacdc.org/index.php/Byzantium
# License: GPLv3

# captive_portal_test.py

from flexmock import flexmock  # http://has207.github.com/flexmock
import unittest
import gateways
import _utils


class GatewaysTest(unittest.TestCase):

    def setUp(self):
        self.mock_template = flexmock()
        self.gateways = gateways.Gateways(self.mock_template, False)

    def test_index(self):
        flexmock(self.gateways).should_receive('set_ethernet_buttons').once.and_return('ethernet')
        flexmock(self.gateways).should_receive('set_wireless_buttons').once.and_return('wireless')
        mock_page = flexmock()
        self.mock_template.should_receive('get_template').with_args(
            '/gateways/index.html').once.and_return(mock_page)
        mock_page.should_receive('render').with_args(title="Network Gateway",
                               purpose_of_page="Configure Network Gateway",
                               ethernet_buttons="ethernet",
                               wireless_buttons="wireless").once
        flexmock(self.gateways).should_receive('update_network_interfaces').once
        self.gateways.index()

    def test_index_failure(self):
        flexmock(self.gateways).should_receive('set_ethernet_buttons').once.and_return('ethernet')
        flexmock(self.gateways).should_receive('set_wireless_buttons').once.and_return('wireless')
        mock_page = flexmock()
        self.mock_template.should_receive('get_template').with_args(
            '/gateways/index.html').once.and_raise(Exception)
        flexmock(self.gateways).should_receive('update_network_interfaces').once
        flexmock(_utils).should_receive('output_error_data').once
        self.gateways.index()

if __name__ == '__main__':
    unittest.main()
