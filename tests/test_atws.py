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
from click.testing import CliRunner

from atws import create_picklist_module



class TestAtws(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_000_something(self):
        pass

    def test_command_line_interface(self):
        runner = CliRunner()
        #         result = runner.invoke(create_picklist_module.main)
        #         assert result.exit_code == 0
        #         assert 'atws.create_picklist_module.main' in result.output
        help_result = runner.invoke(create_picklist_module.main, ['--help'])
        assert help_result.exit_code == 0
        assert 'Show this message and exit.' in help_result.output


if __name__ == '__main__':
    sys.exit(unittest.main())
