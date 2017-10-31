'''
Created on 17 Oct 2015

@author: matt
'''
from __future__ import absolute_import
from suds.sudsobject import Object as sudsobject
from . import monkey_patch
from .. import helpers
from ..constants import DEFAULT_OPTION_NOT_USED



def mp_set_udf(entity, name, value):
    helpers.set_udf(entity._wrapper, entity, name, value)
    

def mp_get_udf_value(entity, name, default=DEFAULT_OPTION_NOT_USED):
    return helpers.get_udf_value(entity._wrapper, entity, name, default)


def mp_del_udf(entity,name):
    helpers.del_udf(entity._wrapper, entity, name)
    

def mp_getattr(entity,attr):
    if attr != 'UserDefinedFields':
        try:
            return helpers.get_udf_value(entity._wrapper,entity,attr)
        except AttributeError:
            raise AttributeError( 'no attribute or udf named {}'.format(attr) )
    return sudsobject.__getattribute__(entity,attr)


def mp_setattr(self,name,value):
    try:
        udf = helpers.get_udf(self._wrapper,self,name)
    except AttributeError:
        sudsobject.__setattr__(self,name,value)
    else:
        udf.Value = value
        

generic_patches = {
   'set_udf':mp_set_udf,
   'get_udf':mp_get_udf_value,
   'del_udf':mp_del_udf,
   '__getattr__':mp_getattr,
   '__setattr__':mp_setattr
   }
monkey_patch.add_generic_patches(generic_patches)
