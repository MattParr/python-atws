'''
Created on 17 Oct 2015

@author: matt
'''
from __future__ import absolute_import
from . import monkey_patch
from ..helpers import get_udf_value, set_udf
from ..constants import DEFAULT_OPTION_NOT_USED
import json

ATTRIBUTE_UDF_NAME = 'AutomatedSystemTags'

def encode(d):
    return json.dumps(d)


def decode(s):
    return json.loads(s)


def del_attribute(wrapper,entity,name):
    #: :type attributes: dict
    attributes = get_attributes(wrapper, entity)
    del attributes[name]
    set_attributes(wrapper, entity, attributes)
    

def get_attribute(wrapper,entity,name,default=DEFAULT_OPTION_NOT_USED):
    attributes = get_attributes(wrapper,entity)
    try:
        result = attributes[name]
    except KeyError:
        if default == DEFAULT_OPTION_NOT_USED:
            raise
        result = set_attribute(wrapper,entity,name,default)
    return result


def get_attributes(wrapper,entity):
    udf_value = get_udf_value(wrapper,entity,ATTRIBUTE_UDF_NAME,json.dumps({}))
    if not udf_value.strip():
        return {}
    return decode(udf_value)


def set_attribute(wrapper,entity,name,value):
    try:
        value = value.isoformat()
    except (KeyError,TypeError,AttributeError):
        pass
    attributes = get_attributes(wrapper,entity)
    attributes[name] = value
    set_attributes(wrapper,entity,attributes)
    return value


def set_attributes(wrapper,entity,attributes):
    udf_value = encode(attributes)
    set_udf(wrapper,entity,ATTRIBUTE_UDF_NAME,udf_value)


def mp_del_attribute(entity,name):
    return del_attribute(entity._wrapper, entity, name)


def mp_set_attribute(entity,name,value):
    return set_attribute(entity._wrapper, entity, name, value)


def mp_set_attributes(entity,attributes):
    return set_attributes(entity._wrapper, entity, attributes)


def mp_get_attribute(entity,name,default=DEFAULT_OPTION_NOT_USED):
    return get_attribute(entity._wrapper, entity, name, default)


def mp_get_attributes(entity):
    return get_attributes(entity._wrapper, entity)

generic_patches = {
   'get_attribute':mp_get_attribute,
   'get_attributes':mp_get_attributes,
   'set_attribute':mp_set_attribute,
   'set_attributes':mp_set_attributes,
   'del_attribute':mp_del_attribute
   }

monkey_patch.add_generic_patches(generic_patches)