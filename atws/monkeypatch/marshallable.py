'''
Created on 10 Jan 2016

@author: matt
'''
from __future__ import absolute_import
from future.utils import iteritems
from builtins import str
import logging
import pytz
from decimal import Decimal
from datetime import datetime
from past.builtins import basestring
from . import monkey_patch
from . import asdict
from ..helpers import localise_datetime

logger = logging.getLogger(__name__)
UTC = pytz.timezone('UTC')
MARSHAL_MAP = {}


def datetime_to_utc_isoformat(dt):
    try:
        return localise_datetime(dt).astimezone(UTC).isoformat()
    except OverflowError:
        return dt.isoformat()
    except Exception:
        logger.exception('failed to isoformat dt: %s', dt)
        raise


def convert(obj):
    result = {}
    for k,v in iteritems(obj):
        if type(v) == list:
            result[k] = []
            for d in v:
                result[k].append(convert(d))
        else:
            result[k] = convert_value(v)
    logger.debug('returning the following dictionary as marshallable')
    logger.debug(result)
    return result


def convert_value(v):
    if isinstance(v, datetime):
        try:
            return datetime_to_utc_isoformat(v)
        except AttributeError:
            return v
    if isinstance(v, basestring):
        try:
            return str(v)
        except TypeError:
            return v
    if isinstance(v, Decimal):
        return str(v)
    return v


def get_marshallable_dict(entity):
    e = entity.asdict()
    return convert(e)


generic_patches = {
   'asmarshallabledict':get_marshallable_dict,
   'asserializabledict':get_marshallable_dict
   }

monkey_patch.add_generic_patches(generic_patches)