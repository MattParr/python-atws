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


def find(index_label, index_name, object_list, condition = always_true):
    index = next(index for (index, d) in enumerate(object_list) 
                if d[index_label] == index_name and condition(d))
    return object_list[index]


def get_field_picklist(field_name, field_info):
    field_picklist = find('Name', 
                          field_name, 
                          field_info.Field)
    return field_picklist


def is_child_field(field_picklist):
    child_parent_field_name = get_child_parent_field_name(field_picklist) 
    return child_parent_field_name is not None


def get_child_parent_field_name(field_picklist):
    parent_field_name = field_picklist.PicklistParentValueField
    return parent_field_name


def get_label_value(label, picklistvalues):
    item = find('Label', label, picklistvalues)
    return item.Value


def get_value_label(value, picklistvalues):
    item = find('Value', id, picklistvalues)
    return item.Label


def get_child_label_value(label, picklistvalues, condition):
    item = find('Label', label, picklistvalues, condition = condition)
    return item.Value


def child_picklist_as_dict(child_picklist):
    child_field_dict = {}
    for item in child_picklist._picklist:
        parent_item_label = child_picklist.parent_item_label
        parent_item_dict = child_field_dict.setdefault(parent_item_label, {})
        parent_item_dict[item.Label] = item.Value
        
    return {child_picklist.entity_type:
            {child_picklist.field_name:child_field_dict}}
    
    
def picklist_as_dict(picklist):
    return {picklist.entity_type:
            {picklist.field_name:
             {item.Label:item.Value for item in picklist._picklist}}}
    
    
class ChildFieldPicklist(object):
    def __init__(self, parent, parent_item_label, field_name):
        self.field_name = field_name
        self._parent = parent
        self.parent_item_label = parent_item_label
        
    
    @property
    def __name__(self):
        return self.child_picklist_name + '_' + self.parent_label
    
    
    @property
    def parent_item_value(self):
        return self._parent[self.parent_label]
    

    @property
    def _picklist(self):
        return self._picklist_info.PicklistValues.PickListValue
    
    
    @property
    def _picklist_info(self):
        return get_field_picklist(self.child_picklist_name, 
                                  self._parent.entity_picklists._field_info)
    
        
    def _condition(self, picklist_value):
        return picklist_value.parentValue == self.parent_item_value
    
    
    def __getitem__(self, item):
        return self.__getattr__(item)
    
    
    def __getattr__(self, attr):
        return get_child_label_value(attr, self._picklist, self._condition)
    
    

class FieldPicklist(object):
    def __init__(self, entity_picklists, field_name):
        self.field_name = field_name
        self.entity_picklists = entity_picklists
        if self.is_child:
            self._children = {}
        
        
    @property
    def entity_type(self):
        return self.entity_picklists.entity_type
    
        
    @property
    def parent(self):
        if self.is_child:
            return self.entity_picklists[self.parent_name]
        else:
            raise AttributeError('field does not have a parent')
        
        
    @property
    def parent_name(self):
        if self.is_child:
            return get_child_parent_field_name(self._picklist_info)
        else:
            raise AttributeError('field does not have a parent')
        
        
    @property
    def __name__(self):
        name = self.entity_type + '_' + self.field_name
        return name
    
        
    @property
    def _picklist(self):
        return self._picklist_info.PicklistValues.PickListValue
    
    
    @property
    def _picklist_info(self):
        return get_field_picklist(self.field_name, 
                                  self._field_info)
        
                
    @property
    def _field_info(self):
        return self.entity_picklists._field_info
    
    
    @property
    def is_child(self):
        return is_child_field(self._picklist_info)


    def lookup(self, label):
        ''' take a field_name_label and return the id'''
        if self.is_child:
            try:
                return self._children[label]
            except KeyError:
                self._children[label] = ChildFieldPicklist(self.parent, 
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
        if self.is_child:
            return child_picklist_as_dict(self)
        else:
            return picklist_as_dict(self)
        
        
    def __call__(self, attr):
        return self.__getattr__(attr)
        
    
    def __getattr__(self,attr):
        return self.lookup(attr)
    
    
    def __getitem__(self,item):
        return self.__getattr__(item)
    
    
    def __str__(self):
        return os.linesep.join(
            [ '{}.{}.{} = {}'.format(self.entity_type,
                                     self.field_name,
                                     field.Label,
                                     field.Value)
            for field in self._picklist]
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
            self._entity_picklist[attr] = FieldPicklist(self, attr)
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
        