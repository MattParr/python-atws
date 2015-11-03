'''
Created on 3 Nov 2015

@author: matt

@todo: cache object passing with default cache storage and with ttl
@todo: monkeypunch lazy picklists into entities by default
@todo: create a switch to turn on automatic picklist value reversal
@todo: update create_picklist_module.py to use this
'''
from atws.helpers import get_picklists, get_field_info


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
            raise AttributeError('{} has no label {}'.format(
                                                             self.__name__,
                                                             label))

    
    def reverse_lookup(self,value):
        result = [k for k,v in self._picklist.iteritems()
                  if v == value]
        if result:
            return result
        else:
            raise ValueError('{} has no value {}'.format(self.__name__,
                                                         value))

        
    def __call__(self,lookup=[]):
        if lookup != []:
            return self.lookup(lookup)
        else:
            return self.as_dict()
        
    
    def __getattr__(self,attr):
        return self.lookup(attr)
    
        
class EntityPicklists(object):
    def __init__(self,entity_type,picklists):
        self._picklists = {}
        self.__name__ = entity_type
        self._entity_type = entity_type
        self.refresh(picklists)
        
        
    def refresh(self,picklists):
        for field_name,picklist in picklists.iteritems():
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
            
        
class Picklists(object):
    def __init__(self,at):
        ':type at: atws.Wrapper'
        self._at = at
        self._entity_types = {}
    
    
    def refresh(self,entity_type):
        field_info = get_field_info(self.at, entity_type)
        #@todo - create an exception if no entity of that type
        picklists = get_picklists(field_info)
        try:
            self._entity_types[entity_type].refresh(picklists)
        except KeyError:
            self._entity_types[entity_type] = EntityPicklists(entity_type,
                                                              picklists)
    
    
    def __getattr__(self,attr):
        try:
            return self._entity_types[attr]
        except KeyError:
            self.refresh(attr)
        return self._entity[attr]
            
            
        