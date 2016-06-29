'''
Created on 10 Jan 2016

@author: matt
'''
from __future__ import absolute_import
from . import monkey_patch
from suds.sudsobject import asdict
from ..helpers import has_udfs, get_udfs, del_user_defined_fields_attribute


def convert_entity_to_dict(entity):
    if has_udfs(entity):
        udfs = get_udfs(entity)
        udfs_list = []
        for udf in udfs:
            udfs_list.append(asdict(udf))
        entity.UserDefinedFields = udfs_list
    else:
        del_user_defined_fields_attribute(entity)
    return asdict(entity)


def mp_as_dict(entity):
    return convert_entity_to_dict(entity)


generic_patches = {
   'asdict':mp_as_dict
   }

monkey_patch.add_generic_patches(generic_patches)