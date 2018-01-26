#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_atws
----------------------------------

Tests for `atws` module.
"""


import sys
import unittest
from contextlib import contextmanager
import atws

query_test_output=u'<?xml version="1.0" ?>\n<queryxml>\n\t<entity>Ticket</entity>\n\t<query>\n\t\t<field>\n\t\t\tStatus\n\t\t\t<expression op="NotEqual">5</expression>\n\t\t</field>\n\t\t<condition>\n\t\t\t<condition operator="OR">\n\t\t\t\t<field>\n\t\t\t\t\tIssueType\n\t\t\t\t\t<expression op="GreaterThan">345</expression>\n\t\t\t\t</field>\n\t\t\t</condition>\n\t\t</condition>\n\t</query>\n</queryxml>\n'

class TestAtws(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_000_zone_lookup_failure(self):
        try:
            _ = atws.connect(username='failed@toresolve.com',
                              password='notright')
        except ValueError as e:
            assert 'failed@toresolve.com failed to resolve to a zone' in str(e) 
    
    
    def test_001_query_building_output(self):
        query = atws.Query('Ticket')
        query.WHERE('Status', query.NotEqual, 5)
        query.open_bracket()
        query.OR('IssueType', query.GreaterThan, 345)
        query_output = query.pretty_print()
        assert repr(query_test_output) == repr(query_output)
        

if __name__ == '__main__':
    sys.exit(unittest.main())
