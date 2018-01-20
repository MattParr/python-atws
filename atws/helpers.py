'''
Created on 27 Sep 2015

@author: matt
'''
from __future__ import absolute_import
from future.utils import iteritems
import logging
import math
from suds import WebFault
from .constants import (AUTOTASK_API_QUERY_RESULT_LIMIT,
                        AUTOTASK_API_TIMEZONE,
                        LOCAL_TIMEZONE,
                        DEFAULT_OPTION_NOT_USED)

logger = logging.getLogger(__name__)


def copy_attributes(from_entity,to_entity):
    attributes = [field[0] for field in from_entity]
    for attribute in attributes:
        setattr(to_entity,attribute,getattr(from_entity,attribute))


def has_udfs(entity):
    try:
        return len(entity.UserDefinedFields.UserDefinedField) >= 1
    except Exception:
        return False


def del_udf(wrapper,entity,name):
    udf = get_udf(wrapper, entity, name)
    udf.Value = ''
    

def get_entity_type(entity):
    return entity.__class__.__name__


def get_udf_value(wrapper,entity,name,default=DEFAULT_OPTION_NOT_USED):
    udf = get_udf(wrapper,entity,name,default)
    try:
        return udf.Value
    except AttributeError:
        if default == DEFAULT_OPTION_NOT_USED:
            raise
        udf.Value = default
    return udf.Value


def get_udfs(entity):
    return entity.UserDefinedFields.UserDefinedField


def get_api_threshold(wrapper):
    result = wrapper.getThresholdAndUsageInfo()
    message = result.EntityReturnInfoResults.EntityReturnInfo[0].Message.split()
    threshold = int(str(message[1]).strip(";"))
    timeframe = int(str(message[3]).strip(";"))
    requests = int(str(message[5]).strip(";"))
    return threshold,timeframe,requests
    
    
def get_api_usage(wrapper):
    threshold,_,requests = get_api_threshold(wrapper)
    return math.ceil( ( float(requests)/float(threshold) )*100 )


def get_udf(wrapper,entity,name,default=DEFAULT_OPTION_NOT_USED):
    if has_udfs(entity):
        for udf in get_udfs(entity):
            if name == udf.Name:
                return udf
    if default == DEFAULT_OPTION_NOT_USED:
        raise AttributeError('no udf named {}'.format(name))
    udf = wrapper.new('UserDefinedField')
    udf.Name = name
    udf.Value = default
    try:
        udf_list = entity.UserDefinedFields.UserDefinedField
    except AttributeError:
        array_of_udfs = wrapper.new('ArrayOfUserDefinedField')
        udf_list = array_of_udfs.UserDefinedField
        entity.UserDefinedFields = array_of_udfs
    udf_list.append(udf)
    return udf


def set_udf(wrapper,entity,name,value):
    udf = get_udf(wrapper,entity, name, value)
    udf.Value = value


def del_user_defined_fields_attribute(entity):
    if hasattr(entity,'UserDefinedFields'):
        delattr(entity,'UserDefinedFields')    


def can_multiupdate_entities(entities):
    True


def entities_have_userdefined_fields(entities):
    for entity in entities:
        if has_udfs(entity):
            return True
    return False


def entities_have_userdefined_fields_with_values(entities):
    for entity in entities:
        if has_udfs(entity):
            for udf in get_udfs(entity):
                value = getattr(udf,'Value',[])
                if value != []:
                    return True
    return False    


def clean_entities(entities):
    for entity in entities:
        clean_entity(entity)
        yield entity


def query_requires_another_call(result,query):
    if not query.get_all_entities:
        return False
    try:
        query.get_query_xml()
    except AttributeError:
        return False
    if query_result_count(result) == AUTOTASK_API_QUERY_RESULT_LIMIT:
        return True
    return False


def get_result_entities(result):
    try:
        return result.EntityResults.Entity
    except Exception:
        return []
    

def get_highest_id(result,field):
    return max(getattr(entity,field) for entity in get_result_entities(result))


def query_result_count(result):
    return len(get_result_entities(result))


def datetime_to_api_timezone(dt):
    if dt.tzinfo is None:
        api_dt = LOCAL_TIMEZONE.localize(dt).astimezone(AUTOTASK_API_TIMEZONE).replace(tzinfo=None)
    else:
        api_dt = dt.astimezone(AUTOTASK_API_TIMEZONE).replace(tzinfo=None)
    return api_dt


def datetime_to_local_timezone(dt):
    if dt.tzinfo is None:
        api_dt = AUTOTASK_API_TIMEZONE.localize(dt).astimezone(LOCAL_TIMEZONE)
    else:
        api_dt = dt.astimezone(LOCAL_TIMEZONE)
    return api_dt


def localise_datetime(dt):
    if dt.tzinfo is None:
        return LOCAL_TIMEZONE.localize(dt)
    else:
        return dt.astimezone(LOCAL_TIMEZONE)


def split_list_into_chunks(list_to_split,chunk_length):
    items = []
    for item in list_to_split:
        if len(items) == chunk_length:
            yield list
            items = []
        items.append(item)
    if items:
        yield items


def clean_udfs(entity):
    new_udf_list = []
    try:
        for udf in entity.UserDefinedFields.UserDefinedField:
            if hasattr(udf,"Value"):
                new_udf_list.append(udf)
        if new_udf_list:
            entity.UserDefinedFields.UserDefinedField = new_udf_list
    except AttributeError:
        pass
    if not new_udf_list:
        del_user_defined_fields_attribute(entity)


def clean_fields(entity):
    remove = list()
    for field_name,field_value in entity:
        if field_name == 'Fields':
            remove.append(field_name)
            continue
        if field_name != 'UserDefinedFields':
            if field_value in ["",None]:
                remove.append(field_name)
    for field in remove:
        delattr(entity,field)


def clean_entity(entity):
    clean_fields(entity)
    clean_udfs(entity)


def process_fields(entity,functions):
    for (field_name,field_value) in entity:
        if field_name in ('Fields','UserDefinedFields'):
            continue
        for fn in functions:
            fn(entity=entity,name=field_name,value=field_value)


def process_udfs(entity,functions):
    try:
        for udf in entity.UserDefinedFields.UserDefinedField:
            for fn in functions:
                fn(entity=entity,udf=udf)
    except AttributeError:
        pass


def process_entity(entity, functions):
    process_fields(entity, functions)
    process_udfs(entity, functions)


def create_userdefined_field_list_items(wrapper,entity,items):
    list_items = [wrapper.new('UserDefinedFieldListItem',**item) 
                  for item in items]
    return wrapper.create(list_items).execute()


def picklist_stream_formatter(s):
    import re
    # Remove invalid characters
    return re.sub('[^0-9a-zA-Z_]', '', s)


def get_field_info(wrapper,entity_type):
    'type: wrapper :atws.Wrapper'
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
    return {field.Name:get_field_picklist(field.PicklistValues.PickListValue) 
     for field in get_field_info_response.Field 
     if has_picklist_values(field)}
                    

def datetime_to_api_timezone_entity(**kwargs):
    try:
        datetime_to_api_timezone(kwargs['udf'].Value)
    except (AttributeError,KeyError,TypeError,OverflowError):
        pass
    else:
        return
    try:
        setattr(kwargs['entity'],
                kwargs['name'],
                datetime_to_api_timezone(kwargs['value']))
    except (AttributeError,KeyError,TypeError,OverflowError):
        pass


def datetime_to_local_timezone_entity(**kwargs):
    try:
        datetime_to_local_timezone(kwargs['udf'].Value)
    except (AttributeError,KeyError,TypeError,OverflowError):
        pass
    else:
        return
    try:
        setattr(kwargs['entity'],
                kwargs['name'],
                datetime_to_local_timezone(kwargs['value']))
    except (AttributeError,KeyError,TypeError,OverflowError):
        pass


def trim_empty_strings_entity(**kwargs):
    try:
        kwargs['udf'].Value = kwargs['udf'].Value.trim()
        if kwargs['udf'].Value == "":
            delattr(kwargs['udf'], 'Value')
    except (AttributeError,KeyError,TypeError):
        pass
    else:
        return
    try:
        setattr(kwargs['entity'],
                kwargs['name'],
                kwargs['value'].trim())
    except (AttributeError,KeyError,TypeError):
        pass
    
    
def trim_single_space_strings_entity(**kwargs):
    try:
        if kwargs['udf'].Value.isspace():
            kwargs['udf'].Value = ''
    except (AttributeError,KeyError,TypeError):
        pass
    else:
        return
    try:
        if getattr(kwargs['entity'], kwargs['name']).isspace():
            setattr(kwargs['entity'],
                    kwargs['name'],
                    '')
    except (AttributeError,KeyError,TypeError):
        pass