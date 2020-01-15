# -*- coding: utf-8 -*-
from __future__ import absolute_import
from pytz import timezone
from .wrapper import connect
from .query import Query

__author__ = 'Matt Parr'
__email__ = 'matt@parr.geek.nz'
__version__ = '0.5.5'

ATWS_API_TIMEZONE = timezone('US/Eastern')
ATWS_ENTITY_SEND_LIMIT = 200
ATWS_ENTITY_RECEIVE_LIMIT = 500
