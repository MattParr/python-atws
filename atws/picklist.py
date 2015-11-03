'''
Created on 3 Nov 2015

@author: matt

@todo: create a picklist object that allows:
preferrably have the wrapper auto generate these objects if needed
but also allow them to be passed in (from a pickle cache later on)
tp = PickList('Ticket')
tp.Status(5) 
'Complete'
tp.Status('Complete')
5
tp.IssueType('ThisIssue')
23455
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
    
    
    def lookup(self,lookup):
        try:
            return self._picklists.get_value(self._entity_type,
                                             self.__name__,
                                             lookup)
        except (KeyError):
            pass
        try:
            return self._picklists.get_label(self._entity_type,
                                             self.__name__,
                                             lookup)
        except (KeyError):
            raise ValueError('lookup not found {}'.format(lookup))
            
        
    def __call__(self,lookup=[]):
        if lookup != []:
            return self.lookup(lookup)
        else:
            return self.as_dict()
        
    
    def __getattr__(self,attr):
        try:
            return self._picklist[attr]
        except KeyError:
            raise AttributeError(
                '{} picklist has no label {}'.format(self.__name__,attr)
                )
    
        
class EntityPicklists(object):
    def __init__(self,entity_type,picklists):
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
            
            
class Picklists(object):
    def __init__(self,at):
        ':param at: atws.Wrapper'
        self._at = at
        self._entity_types = {}
    
    def refresh(self,entity_type):
        field_info = get_field_info(self.at, entity_type)
        picklists = get_picklists(field_info)
        try:
            self._entity_types[entity_type].refresh(picklists)
        except KeyError:
            self._entity_types[entity_type] = EntityPicklists(entity_type,
                                                              picklists)
        