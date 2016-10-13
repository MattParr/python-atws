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
from cached_property import cached_property
from .helpers import get_field_info


def always_true(*args):
    return True


def get_index(index_label, index_name, object_list, condition = None):
    if condition is None:
        condition = always_true
    index = next(index for (index, d) in enumerate(object_list) 
                if d[index_label] == index_name and condition(d))
    return index


def get_field_picklist(field_name, field_info):
    field_picklist = field_info.Field[get_index('Name', 
                                                field_name, 
                                                field_info.Field)]
    return field_picklist


def is_child_field(field_picklist):
    child_parent_field_name = get_child_parent_field_name(field_picklist) 
    return child_parent_field_name is not None


def get_child_parent_field_name(field_picklist):
    parent_field_name = field_picklist.PicklistParentValueField
    return parent_field_name


def get_label_value(label, picklistvalues):
    item = picklistvalues[get_index('Label', label, picklistvalues)]
    return item.Value


def get_value_label(value, picklistvalues):
    item = picklistvalues[get_index('Value', id, picklistvalues)]
    return item.Label


def get_child_label_value(label, picklistvalues, condition):
    item = picklistvalues[get_index('Label', label, picklistvalues, 
                                    condition = condition)]
    return item.Value


class ChildEntityPicklist(object):
    def __init__(self, parent, parent_label, child_picklist_name):
        self.child_picklist_name = child_picklist_name
        self._parent = parent
        self.parent_label = parent_label
        
    
    @property
    def __name__(self):
        return self.child_picklist_name + '_' + self.parent_label
    
    
    @property
    def parent_value(self):
        return self._parent[self.parent_label]
    

    @property
    def _picklist(self):
        return self._picklist_info.PicklistValues.PickListValue
    
    
    @property
    def _picklist_info(self):
        return get_field_picklist(self.child_picklist_name, 
                                  self._parent.entity_picklists._field_info)
    
        
    def _condition(self, picklist_value):
        return picklist_value.parentValue == self.parent_value
    
    
    def __getitem__(self, item):
        return self.__getattr__(item)
    
    
    def __getattr__(self, attr):
        return get_child_label_value(attr, self._picklist, self._condition)
    
    

class EntityPicklist(object):
    def __init__(self, entity_picklists, field_name):
        self.field_name = field_name
        self.entity_picklists = entity_picklists
        if self.is_child:
            self._children = {}
        
        
    @property
    def __name__(self):
        name = self.entity_picklists.entity_type + '_' + self.field_name
        return name
    
        
    @property
    def _picklist(self):
        return self._picklist_info.PicklistValues.PickListValue
    
    
    @property
    def _picklist_info(self):
        return get_field_picklist(self.field_name, 
                                  self.entity_picklists._field_info)
        
                
    @property
    def is_child(self):
        return is_child_field(self._picklist_info)


    def lookup(self, label):
        ''' take a field_name_label and return the id'''
        if self.is_child:
            try:
                return self._children[label]
            except KeyError:
                parent_name = get_child_parent_field_name(self._picklist_info)
                parent = self.entity_picklists[parent_name]
                self._children[label] = ChildEntityPicklist(parent, 
                                                            label, 
                                                            self.field_name) 
                return self._children[label]
        else:
            return get_label_value(label, self._picklist)

    
    def reverse_lookup(self, value):
        ''' take a field_name_id and return the label '''
        label = get_value_label(value, self._picklist)
        if self.is_child:
            self.lookup(label)
        else:
            return label 


    def as_dict(self):
        return {self._entity_type:{self._field_name:self._picklist}}
    
        
    def __call__(self, attr):
        return self.__getattr__(attr)
        
    
    def __getattr__(self,attr):
        return self.lookup(attr)
    
    
    def __getitem__(self,item):
        return self.__getattr__(item)
    
    
    def __str__(self):
        return os.linesep.join(
            [ '{}.{}.{} = {}'.format(self._entity_type,
                                     self._field_name,
                                     k,
                                     v)
            for k,v in iteritems(self._picklist)]
                               )
    
        
class EntityPicklists(object):
    def __init__(self,at, entity_type):
        self._at = at
        self.entity_type = entity_type
        self._entity_picklist = {}
    
    
    @property
    def __name__(self):
        return self.entity_type
    
        
    @cached_property
    def _field_info(self):
        result = get_field_info(self._at, self.entity_type) 
        return result
        
        
    def refresh(self,picklists):
        del self._field_info
        
            
    def __getattr__(self,attr):
        try:
            return self._entity_picklist[attr]
        except KeyError:
            self._entity_picklist[attr] = EntityPicklist(self, attr)
            return self._entity_picklist[attr]
            
        
    def __getitem__(self, item):
        return self.__getattr__(item)
        
        
class Picklists(object):
    def __init__(self,at):
        self._at = at
        self._entity_picklists = {}
    
    
    def refresh(self,entity_type):
        self._entity_picklists[entity_type].refresh()
            
    
    def __getattr__(self,attr):
        try:
            entity_picklists = self._entity_picklists[attr]
        except KeyError:
            entity_picklists = EntityPicklists(self._at, attr)
            self._entity_picklists[attr] = entity_picklists 
        return entity_picklists
            
            
    def __getitem__(self, item):
        return self.__getattr__(item)
        