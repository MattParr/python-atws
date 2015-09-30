'''
Created on 27 Sep 2015

@author: matt
'''
def has_udf(entity):
    try:
        if entity.UserDefinedFields.UserDefinedField[0]:
            return True
    except Exception:
        return False


def del_user_defined_fields_attribute(entity):
    if hasattr(entity,'UserdefinedFields'):
        delattr(entity,'UserDefinedFields')    


def can_multiupdate_entities(entities):
    if entities_have_userdefined_fields(entities):
        return False
    return True


def entities_have_userdefined_fields(entities):
    for entity in entities:
        if has_udf(entity):
            return True
    return False


def clean_entities(entities):
    for entity in entities:
        clean_entity(entity)


def clean_udfs(entity):
    if not has_udf(entity):
        del_user_defined_fields_attribute(entity)
        return
    new_udf_list = []
    for udf in entity.UserDefinedFields.UserDefinedField:
        if getattr(udf,"Value",None) == None:
            continue
        new_udf_list.append(udf)
    if new_udf_list:
        entity.UserDefinedFields.UserDefinedField = new_udf_list


def clean_entity(entity):
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
    clean_udfs(entity)
    

def api_datetime_string(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def split_entities_into_packet_lengths(entities,packet_length):
    for i in xrange(0, len(entities), packet_length):
        yield entities[i:i+packet_length]
        
