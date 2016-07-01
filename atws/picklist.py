'''
Created on 3 Nov 2015

@author: matt

@todo: cache object passing with default cache storage and with ttl
@todo: monkeypunch lazy picklists into entities by default
@todo: create a switch to turn on automatic picklist value reversal
@todo: update create_picklist_module.py to use this
'''
from __future__ import absolute_import
from future.utils import iteritems
import os
from .helpers import get_picklists, get_field_info


class EntityPicklist(object):
    def __init__(self,entity_type,field_name,picklist):
        self.__name__ = entity_type + '.' + field_name
        self._field_name = field_name
        self._entity_type = entity_type
        self._picklist = picklist


    def as_dict(self):
        return {self._entity_type:{self._field_name:self._picklist}}
    
    
    def lookup(self,label):
        try:
            return self._picklist[label]
        except KeyError:
            raise ValueError('{} has no label {}'.format(
                                                             self.__name__,
                                                             label))

    
    def reverse_lookup(self,value):
        return [k for k,v in iteritems(self._picklist)
                  if v == str(value)]

        
    def __call__(self,lookup=[]):
        if lookup != []:
            return self.lookup(lookup)
        else:
            return self.as_dict()
        
    
    def __getattr__(self,attr):
        try: 
            return self.lookup(attr)
        except ValueError as e:
            raise AttributeError(e)
    
    
    def __getitem__(self,item):
        return self._picklist[item]
    
    
    def __str__(self):
        return os.linesep.join(
            [ '{}.{}.{} = {}'.format(self._entity_type,
                                     self._field_name,
                                     k,
                                     v)
            for k,v in iteritems(self._picklist)]
                               )
    
        
class EntityPicklists(object):
    def __init__(self,entity_type,picklists):
        self._picklists = {}
        self.__name__ = entity_type
        self._entity_type = entity_type
        self.refresh(picklists)
        
        
    def refresh(self,picklists):
        for field_name,picklist in iteritems(picklists):
            self._update_picklist_object(field_name, picklist)
        
    
    def _update_picklist_object(self,field_name, picklist):
        try:
            self._picklists[field_name].__init__(self._entity_type,
                                                 field_name,
                                                 picklist)
        except KeyError:
            self._picklists[field_name] = EntityPicklist(self._entity_type,
                                                         field_name,
                                                         picklist)
            
            
    def __getattr__(self,attr):
        try:
            return self._picklists[attr]
        except KeyError:
            raise AttributeError('{} has no field {}'.format(self._entity_type,
                                                            attr))
            
        
    def __getitem__(self, item):
        return self._picklists[item]
        
        
class Picklists(object):
    def __init__(self,at):
        ':type at: atws.Wrapper'
        self._at = at
        self._entity_types = {}
    
    
    def refresh(self,entity_type):
        field_info = get_field_info(self._at, entity_type)
        #@todo - create an exception if no entity of that type
        #suds.WebFault: Server raised fault: 'System.Web.Services.Protocols.SoapException: Server was unable to process request. ---> System.NullReferenceException: Object reference not set to an instance of an object.
        #at autotask.web.services.API.ATWSProcessor.GetFieldInfo(String psObjectType)
        #at autotask.web.services.API.v1_5.ATWS.GetFieldInfo(String psObjectType)
        #--- End of inner exception stack trace ---'
        picklists = get_picklists(field_info)
        try:
            self._entity_types[entity_type].refresh(picklists)
        except KeyError:
            self._entity_types[entity_type] = EntityPicklists(entity_type,
                                                              picklists)
        return self._entity_types[entity_type]
    
    
    def __getattr__(self,attr):
        try:
            return self._entity_types[attr]
        except KeyError:
            self.refresh(attr)
        return self._entity_types[attr]
            
            
    def __getitem__(self, item):
        return self.__getattr__(item)
        