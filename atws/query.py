from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from helpers import format_datetime_for_api_query,split_list_into_chunks
from constants import AUTOTASK_API_QUERY_ID_LIMIT


def get_id_query(entity_type,id_list):
    query = Query()
    query.setEntity(entity_type)
    for entity_id in id_list:
        query.OR('id',query.Equals,entity_id)
    return query
    

def get_queries_for_entities_by_id(entity_type,
                                   id_list,
                                   id_limit=AUTOTASK_API_QUERY_ID_LIMIT,
                                   query_function=get_id_query):
    id_lists = split_list_into_chunks(id_list,AUTOTASK_API_QUERY_ID_LIMIT)
    return [query_function(entity_type,id_list) for id_list in id_lists]


class Query(object):
    Equals='Equals'
    NotEqual='NotEqual'
    GreaterThan='GreaterThan'
    LessThan='LessThan'
    GreaterThanorEquals='GreaterThanorEquals'
    LessThanOrEquals='LessThanOrEquals'
    BeginsWith='BeginsWith'
    EndsWith='EndsWith'
    Contains='Contains'
    IsNotNull='IsNotNull'
    IsNull='IsNull'
    IsThisDay='IsThisDay'
    Like='Like'
    NotLike='NotLike'
    SoundsLike='SoundsLike'


    def FROM(self,entity_type):
        self.entity_type = entity_type

        
    def WHERE(self,field_name,field_condition,field_value,udf=False):
        self._add_field(None, field_name, field_condition, field_value, udf)

    
    def OR(self,field_name,field_condition,field_value,udf=False):
        self._add_field('OR', field_name, field_condition, field_value, udf)
    
    
    def AND(self,field_name,field_condition,field_value,udf=False):
        self._add_field(None, field_name, field_condition, field_value, udf)
        
        
    def open_bracket(self,operator=None):
        attrib = {}
        if operator:
            attrib = {'operator':operator}
        parent = self.cursor
        self.cursor = SubElement(parent,'condition',attrib=attrib)
        self.cursor.parent = parent
    
    
    def close_bracket(self):
        self.cursor = self.cursor.parent
        

    def reset(self):
        self.cursor = self.query
        self.query.clear()
        self.minimum_id_xml = None
        self.minimum_id = None
        self.minimum_id_field = 'id'

    
    def get_query_xml(self):
        self.entityxml.text = self.entity_type
        if self.minimum_id:
            self._add_min_id_field()
        return tostring(self.queryxml)
    
    
    def pretty_print(self):
        import xml.dom.minidom
        return xml.dom.minidom.parseString(self.get_query_xml()).toprettyxml()
    
    
    def set_minimum_id(self,minimum_id,field='id'):
        self.minimum_id = minimum_id
        self.minimum_id_field = field


    def _add_field(self,operator,field_name,field_condition,field_value,udf=False):
        attributes = {}
        if udf:
            attributes['udf'] = 'true' 
        self.open_bracket(operator)
        field = SubElement(self.cursor,'field', attrib=attributes)
        field.text = field_name
        expression = SubElement(field,'expression',attrib={'op':field_condition})
        expression.text = self._process_field_value(field_value)
        self.close_bracket()
        return field,expression
                    
        
    def _add_min_id_field(self):
        try:
            self._update_min_id_xml()
        except AttributeError:
            self._create_min_id_xml()
            
    
    def _update_min_id_xml(self):
        self.minimum_id_xml.text = self._process_field_value(self.minimum_id)
    
    
    def _create_min_id_xml(self):
        minimum_id = self._process_field_value(self.minimum_id)
        expression = self._add_field(None, 
                                     self.minimum_id_field, 
                                     self.GreaterThan, 
                                     minimum_id)[1]
        self.minimum_id_xml = expression
    
    
    def _process_field_value(self,value):
        if type(value) is datetime:
            return format_datetime_for_api_query(value)
        return str(value)
    
    
    def __init__(self,entity_type = None):
        self.entity_type = entity_type
        self.queryxml = Element('queryxml')
        self.entityxml = SubElement(self.queryxml, 'entity')
        self.query = SubElement(self.queryxml, 'query')
        self.reset()


    def __str__(self):
        return repr(self.get_query_xml())
    