'''
Created on 3 Nov 2015

@author: matt

@todo: monkeypunch lazy picklists into entities by default combined with below
@todo: create a switch to turn on automatic picklist value reversal
@todo: update create_picklist_module.py to use this and child naming 
'''
from __future__ import absolute_import
import os
from cached_property import cached_property
from .helpers import get_field_info
import logging
logger = logging.getLogger(__name__)

def is_inactive(*args):
    return is_active(*args) != True


def is_active(*args):
    return args[0]['IsActive']
    
    
def always_true(*args):
    return True


def find(index_label, index_name, object_list, condition = always_true):
    try:
        return next(obj for obj in object_list 
                    if obj[index_label] == index_name and condition(obj))   
    except StopIteration:
        raise KeyError('label not found in index', index_label, index_name)
    

def get_field_picklist(field_name, field_info):
    field_picklist = find('Name', 
                          field_name, 
                          field_info.Field)
    # Convert Picklist Values to int
    # See issue: https://github.com/MattParr/python-atws/issues/53
    for item in field_picklist.PicklistValues:
        for picklist_value in item[1]:
            setattr(picklist_value, 'Value', int(picklist_value.Value))

    return field_picklist


def is_child_field(field_picklist):
    child_parent_field_name = get_child_parent_field_name(field_picklist) 
    return child_parent_field_name is not None


def get_child_parent_field_name(field_picklist):
    try:
        parent_field_name = field_picklist.PicklistParentValueField
    except AttributeError: 
        parent_field_name = None
    return parent_field_name


def get_label_value(label, picklistvalues, condition=is_active):
    item = find('Label', label, picklistvalues, condition=condition)
    return item.Value


def get_value_label(value, picklistvalues, condition=is_active):
    item = find('Value', value, picklistvalues, condition=condition)
    return item.Label


def get_child_label_value(label, picklistvalues, condition):
    item = find('Label', label, picklistvalues, condition = condition)
    return item.Value


def child_picklist_as_dict(child_picklist):
    child_field_dict = {}
    parent = child_picklist.parent
    if child_picklist.is_active == True:
        condition = is_active
    elif child_picklist.is_active == False:
        condition = is_inactive
    else:
        condition = always_true
        
    for item in child_picklist._picklist:
        try:
            parent_item_label = parent.reverse_lookup(item.parentValue,
                                                  condition=condition)
        except KeyError:
            logger.debug('inactive parent item: %s',
                         item.parentValue)
        else:
            parent_item_dict = child_field_dict.setdefault(parent_item_label, 
                                                           dict())
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
        return self._parent[self.parent_item_label]
    

    @property
    def _picklist(self):
        return self._picklist_info.PicklistValues.PickListValue
    
    
    @property
    def _picklist_info(self):
        return get_field_picklist(self.field_name, 
                                  self._parent.entity_picklists._field_info)
    
        
    def _condition(self, picklist_value):
        return (picklist_value.parentValue == self.parent_item_value 
                and is_active(picklist_value))
    
    
    def lookup(self, label):
        return get_child_label_value(label, self._picklist, self._condition)
    
    
    def __getitem__(self, item):
        return self.lookup(item)
    
    
    def __call__(self, label):
        return self.lookup(label)
    

class FieldPicklist(object):
    def __init__(self, entity_picklists, field_name):
        self.field_name = field_name
        self.entity_picklists = entity_picklists
        self.is_active = None
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
        picklist_values = self._picklist_info.PicklistValues.PickListValue
        if self.is_active != None:
            return [picklist_value for picklist_value in picklist_values 
                    if picklist_value.IsActive == self.is_active]
        else:
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

    
    def reverse_lookup(self, value, condition=is_active):
        ''' take a field_name_id and return the label '''
        label = get_value_label(int(value), self._picklist, condition=condition)
        return label 


    def as_dict(self):
        if self.is_child:
            return child_picklist_as_dict(self)
        else:
            return picklist_as_dict(self)
        
        
    def __call__(self, label):
        return self.lookup(label)
        
    
    def __getitem__(self,item):
        return self.lookup(item)
    
    
    def __str__(self):
        return os.linesep.join(
            [ '{}.{}.{} = {}'.format(self.entity_type,
                                     self.field_name,
                                     field.Label,
                                     field.Value)
            for field in self._picklist]
                               )
        
    
    def __iter__(self):
        return iter([field for field in self._picklist])
    
        
class EntityPicklists(object):
    def __init__(self,at, entity_type):
        self._at = at
        self.entity_type = entity_type
        self._entity_fields = {}
    
    
    @property
    def __name__(self):
        return self.entity_type
    
        
    @cached_property
    def _field_info(self):
        result = get_field_info(self._at, self.entity_type) 
        return result
        
        
    @cached_property
    def fields(self):
        return [field for field in self._field_info.Field]
            
    
    @cached_property            
    def picklist_fields(self):
        return [field for field in self.fields if 
                field.IsPickList]
        
        
    def refresh(self,picklists=None):
        del self._field_info
        
            
    def lookup(self,field):
        try:
            return self._entity_fields[field]
        except KeyError:
            self._entity_fields[field] = FieldPicklist(self, field)
            return self._entity_fields[field]
            
        
    def __getitem__(self, item):
        return self.lookup(item)
    
    
    def __call__(self, field):
        return self.lookup(field)
    
    
    def __iter__(self):
        return iter([self.lookup(field.Name) for field in self.picklist_fields])
        
        
class Picklists(object):
    def __init__(self,at):
        self._at = at
        self._entity_picklists = {}
    
    
    def refresh(self,entity_type):
        self._entity_picklists[entity_type].refresh()
            
    
    def lookup(self,entity):
        try:
            entity_picklists = self._entity_picklists[entity]
        except KeyError:
            entity_picklists = EntityPicklists(self._at, entity)
            self._entity_picklists[entity] = entity_picklists 
        return entity_picklists
            
            
    def __getitem__(self, item):
        return self.lookup(item)
    
    
    def __call__(self, entity):
        return self.lookup(entity)
    
    
    def __iter__(self):
        return iter(self._entity_picklists)
        
 
