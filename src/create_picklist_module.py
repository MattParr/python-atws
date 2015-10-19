#!/bin/env python
import atws
import os
import argparse
import re

csnregex = re.compile('^\d+$')

parser = argparse.ArgumentParser(description='test')
parser.add_argument('target_path')
parser.add_argument('--username', default=os.environ.get('AUTOTASK_API_USERNAME', None))
parser.add_argument('--password', default=os.environ.get('AUTOTASK_API_PASSWORD', None))
parser.add_argument('--url', default=os.environ.get('AUTOTASK_API_URL', None))

args = parser.parse_args()
if not args.username or not args.password:
    exit(parser.print_usage())


username = os.environ['AUTOTASK_API_USERNAME']
password = os.environ['AUTOTASK_API_PASSWORD']
url = os.environ.get('AUTOTASK_API_URL',None)

at = atws.connect(url=url,username=username,password=password)

class PickList(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)


    def __setattr__(self, name, value):
        self[name] = value


    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)

#also create an object that allows:
#preferrably have the wrapper auto generate these objects if needed
#but also allow them to be passed in (from a pickle cache later on)
tp = PickList('Ticket')
tp.Status(5) 
'Complete'
tp.Status('Complete')
5
tp.IssueType('ThisIssue')
23455




def cvn(s):
    # Remove leading characters until we find a letter or underscore
    s = re.sub('^[^a-zA-Z_]+', '', s)
    # Remove invalid characters
    return re.sub('[^0-9a-zA-Z_]', '', s)


def get_field_info(wrapper,entity_type):
    fields = wrapper.new('GetFieldInfo')
    fields.psObjectType = entity_type
    return wrapper.GetFieldInfo(fields)


def has_picklist_values(field):
    if field.IsPickList:
        if field.PicklistValues:
            return True
    return False
        

def get_field_picklist(picklist_values):
    return {obj.Label:obj.Value for obj in picklist_values}


def get_picklists(get_field_info_response):
    return {field:get_field_picklist(field.PicklistValues.PickListValue) 
     for field in get_field_info_response.Field 
     if has_picklist_values(field)}
    

def get_picklist_stream(entity_type,picklists):
    for picklist_name,picklist in picklists.iteritems():
        for field_name,field_value in picklist.iteritems():
            yield "{}_{}_{} = {}\n".format(cvn(entity_type),
                                           cvn(picklist_name),
                                           cvn(field_name),
                                           repr(field_value)
                                           )


