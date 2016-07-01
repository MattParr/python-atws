'''
Created on 17 Oct 2015

@author: matt
@todo: check if simply patching 'Entity' class is enough for the Entity patches
'''
from future.utils import iteritems
BLACKLISTED_TYPES = [
    'ATWSError',
    'ATWSResponse',
    'ATWSZoneInfo',
    'ArrayOfATWSError',
    'ArrayOfEntity',
    'ArrayOfEntityInfo',
    'ArrayOfEntityReturnInfo',
    'ArrayOfField',
    'ArrayOfPickListValue',
    'ArrayOfUserDefinedField',
    'Entity',
    'EntityDuplicateStatus',
    'EntityInfo',
    'EntityReturnInfo',
    'EntityReturnInfoDatabaseAction',
    'Field',
    'PickListValue',
    'UserDefinedField',
    ]
    
def get_api_types(suds_object,blacklist = []):
    return [sudtype[0].name 
            for sudtype 
            in suds_object.sd[0].types 
            if sudtype[0].name not in blacklist]


def get_api_objects(suds_object,blacklist = []):
    types = get_api_types(suds_object, blacklist) 
    return [suds_object.factory.create(t) for t in types]


def get_api_classes(suds_object,blacklist = []):
    objects = get_api_objects(suds_object, blacklist)
    return [obj.__class__ for obj in objects]


def monkey_patch(obj,patch_name,patch_obj):
    setattr(obj,patch_name,patch_obj)


class DuckPunch(object):

    
    GENERIC_PATCHES = []
    SPECIFIC_PATCHES = []

    def add_generic_patches(self,patches):
        self.GENERIC_PATCHES.append(patches)
        
        
    def add_specific_patches(self,patches):
        self.SPECIFIC_PATCHES.append(patches)

    
    def __call__(self,wrapper):
        self._process_wrapper(wrapper)
        
        
    def _process_wrapper(self,wrapper):
        self._wrapper = wrapper
        self._wrapper._mp = self
        
        entity_classes = get_api_classes(wrapper.client,BLACKLISTED_TYPES)
        for entity_class in entity_classes:
            self._patch_class(entity_class)
            
            
    def _patch_class(self,entity_class):
        entity_class._wrapper = self._wrapper
        self._specific_patch(entity_class)
        self._generic_patch(entity_class)
        
    
    def _generic_patch(self,entity_class):
        entity_class._wrapper = self._wrapper
        for patches in self.GENERIC_PATCHES:
            for attr_name,attr_obj in iteritems(patches):
                monkey_patch(entity_class,attr_name,attr_obj)
        
    
    def _specific_patch(self,entity_class):
        for patches in self.SPECIFIC_PATCHES:
            for attr_name,attr_obj in patches.get(entity_class.__name__,{}):
                monkey_patch(entity_class,attr_name,attr_obj)
            
    
