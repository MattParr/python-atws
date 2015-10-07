import helpers
from suds.sudsobject import Object as sudsobject

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


def set_udf(entity, name, value):
    helpers.set_udf(entity._wrapper, entity, name, value)
    

def get_udf_value(entity,name):
    return helpers.get_udf_value(entity._wrapper, entity, name)


def del_udf(entity,name):
    helpers.del_udf(entity._wrapper, entity, name)
    

def __getattr(entity,attr):
    if attr != 'UserDefinedFields':
        try:
            return helpers.get_udf_value(entity._wrapper,entity,attr)
        except AttributeError:
            raise AttributeError('no attribute or udf named %s',attr)
    return sudsobject.__getattribute__(attr)


def __setattr(self,name,value):
    try:
        udf = helpers.get_udf(self._wrapper,self,name)
    except AttributeError:
        sudsobject.__setattr__(self,name,value)
    else:
        udf.Value = value
        
    
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
    'InstalledProductType',
    'InstalledProductTypeUdfAssociation',
    'PickListValue',
    'UserDefinedField',
    'UserDefinedFieldDefinition',
    'UserDefinedFieldListItem',
    ]

GENERIC_PATCHES = {
                   'set_udf':set_udf,
                   'get_udf':get_udf_value,
                   'del_udf':del_udf,
                   '__getattr__':__getattr,
                   '__setattr__':__setattr
                   }


def monkey_patch(obj,patch_name,patch_obj):
    setattr(obj,patch_name,patch_obj)
    

class MonkeyPatch(object):
    def __init__(self,wrapper,**kwargs):
        self._kwargs = kwargs
        self._process_wrapper(wrapper)
        
        
    def _process_wrapper(self,wrapper):
        self._wrapper = wrapper
        self._wrapper._mp = self
        
        entity_classes = get_api_classes(wrapper.client,BLACKLISTED_TYPES)
        for entity_class in entity_classes:
            self.patch_class(entity_class)
            
            
    def patch_class(self,entity_class):
        entity_class._wrapper = self._wrapper
        self.generic_patch(entity_class)
        self.specific_patch(entity_class)
        
    
    def generic_patch(self,entity_class):
        entity_class._wrapper = self._wrapper
        for attr_name,attr_obj in GENERIC_PATCHES.iteritems():
            monkey_patch(entity_class,attr_name,attr_obj)
        
    
    def specific_patch(self,entity_class):
        pass
    
    