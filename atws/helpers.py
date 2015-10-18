'''
Created on 27 Sep 2015

@author: matt
'''
import query as q
from constants import (AUTOTASK_API_QUERY_DATEFORMAT,
                       AUTOTASK_API_QUERY_RESULT_LIMIT,
                       AUTOTASK_API_TIMEZONE,
                       LOCAL_TIMEZONE)


def copy_attributes(from_entity,to_entity):
    attributes = [field[0] for field in from_entity]
    for attribute in attributes:
        setattr(to_entity,attribute,getattr(from_entity(attribute)))

                       
def has_udfs(entity):
    try:
        return len(entity.UserDefinedFields.UserDefinedField) >= 1
    except Exception:
        return False


def del_udf(wrapper,entity,name):
    udf = get_udf(wrapper, entity, name)
    entity.UserDefinedFields.UserDefinedField.remove(udf)
    

def get_entity_type(entity):
    return entity.__class__.__name__


def get_udf_value(wrapper,entity,name,default=[]):
    return get_udf(wrapper,entity,name,default).Value


def get_udf(wrapper,entity,name,default=[]):
    if has_udfs(entity):
        for udf in entity.UserDefinedFields.UserDefinedField:
            if name == udf.Name:
                return udf
    if default == []:
        raise AttributeError('no udf named {}'.format(name))
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



def get_entities_by_field_equals(wrapper,entity_type,field,value,udf=False):
    query = q.Query(entity_type)
    query.WHERE(field,query.Equals,value,udf)
    return wrapper.query(query)    


def get_entity_by_id(wrapper,entity_type,entity_id):
    result = get_entities_by_field_equals(wrapper, 
                                          entity_type, 
                                          'id', 
                                          entity_id, 
                                          False)
    return result[0]


def get_userdefined_field_list_items(wrapper,entity):
    query = q.Query('UserDefinedFieldListItem')
    query.WHERE('UdfFieldId', query.Equals, entity.id)
    return wrapper.query(query)


def create_userdefined_field_list_items(wrapper,entity,items):
    list_items = [wrapper.new('UserDefinedFieldListItem',**item) 
                  for item in items]
    return wrapper.create(list_items)

    
    
