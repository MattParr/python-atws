'''
Created on 27 Sep 2015

@author: matt
'''
from constants import (AUTOTASK_API_QUERY_DATEFORMAT,
                       AUTOTASK_API_QUERY_RESULT_LIMIT,
                       AUTOTASK_API_TIMEZONE,
                       LOCAL_TIMEZONE)
                       
def has_udfs(entity):
    try:
        entity.UserDefinedFields.UserDefinedField[0]
    except Exception:
        return False
    else:
        return True


def del_udf(wrapper,entity,name):
    udf = get_udf(wrapper, entity, name)
    entity.UserDefinedFields.UserDefinedField.remove(udf)
    

def get_udf_value(wrapper,entity,name):
    return get_udf(wrapper,entity,name).Value


def get_udf(wrapper,entity,name,default=[]):
    if has_udfs(entity):
        for udf in entity.UserDefinedFields.UserDefinedField:
            if name == udf.Name:
                return udf
    if default == []:
        raise AttributeError('no udf named %s',name)
    udf = wrapper.new('UserDefinedField')
    udf.Name = name
    udf.Value = default
    entity.UserDefinedFields.UserDefinedField.append(udf)
    return udf


def set_udf(wrapper,entity,name,value):
    udf = get_udf(wrapper,entity, name, value)
    udf.Value = value


def del_user_defined_fields_attribute(entity):
    if hasattr(entity,'UserdefinedFields'):
        delattr(entity,'UserDefinedFields')    


def can_multiupdate_entities(entities):
    if entities_have_userdefined_fields(entities):
        return False
    return True


def entities_have_userdefined_fields(entities):
    for entity in entities:
        if has_udfs(entity):
            return True
    return False


def clean_entities(entities):
    for entity in entities:
        clean_entity(entity)


def query_requires_another_call(result,query):
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


def format_datetime_for_api_query(dt):
    return localise_datetime(dt).strftime(AUTOTASK_API_QUERY_DATEFORMAT)


def localise_datetime(dt):
    if dt.tzinfo is None:
        api_dt = LOCAL_TIMEZONE.localize(dt).astimezone(AUTOTASK_API_TIMEZONE)
    else:
        api_dt = dt.astimezone(AUTOTASK_API_TIMEZONE)
    return api_dt


def split_list_into_chunks(list_to_split,chunk_length):
    for i in xrange(0, len(list_to_split), chunk_length):
        yield list_to_split[i:i+chunk_length]


def clean_udfs(entity):
    new_udf_list = []
    try:
        for udf in entity.UserDefinedFields.UserDefinedField:
            if hasattr(udf,"Value"):
                continue
            new_udf_list.append(udf)
        if new_udf_list:
            entity.UserDefinedFields.UserDefinedField = new_udf_list
    except AttributeError:
        pass
    if not new_udf_list:
        del_user_defined_fields_attribute(entity)


def clean_fields(entity):
    remove = list()
    for field in entity:
        if field[0] == 'Fields':
            remove.append(field[0])
            continue            
        if field[0] != 'UserDefinedFields':
            if getattr(entity,field[0],"") in ["",None]:
                remove.append(field[0])
                continue
    for field in remove:
        delattr(entity,field)            
                
                
def clean_entity(entity):
    clean_fields(entity)     
    clean_udfs(entity)
    

def api_datetime_string(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

        
