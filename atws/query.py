from __future__ import absolute_import
import sys
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.sax.saxutils import escape
from .helpers import datetime_to_api_timezone
from .constants import (AUTOTASK_API_QUERY_ID_LIMIT,
                        AUTOTASK_API_QUERY_DATEFORMAT,
                        WRAPPER_DEFAULT_GET_ALL_ENTITIES)

PY3 = sys.version_info >= (3, 0)
QUERY_ENCODING = None
if PY3:
    QUERY_ENCODING = 'unicode'


XML_QUERY_ESCAPE = { '"' : '&quot;',
                     "'" : '&apos;'}

def get_userdefined_field_list_items(wrapper,entity):
    query = Query('UserDefinedFieldListItem')
    query.WHERE('UdfFieldId', query.Equals, entity.id)
    return wrapper.query(query).fetch_all()


def get_entity_by_id(wrapper,entity_type,entity_id):
    result = get_entities_by_field_equals(wrapper,
                                          entity_type,
                                          'id',
                                          entity_id,
                                          False)
    for i, e in enumerate(result):
        first_entity = e
        if i == 1:
            raise ValueError('too many results')
    return first_entity
        

def get_entities_by_field_equals(wrapper,entity_type,field,value,udf=False):
    query = Query(entity_type)
    query.WHERE(field,query.Equals,value,udf)
    return wrapper.query(query) 


def format_datetime_for_api_query(dt):
    return datetime_to_api_timezone(dt).strftime(AUTOTASK_API_QUERY_DATEFORMAT)


def query_escape(value):
    return escape(value, XML_QUERY_ESCAPE)

    
def get_id_query(entity_type,id_list):
    query = Query(entity_type)
    for entity_id in id_list:
        query.OR('id',query.Equals,entity_id)
    return query
    

def get_queries_for_entities_by_id(entity_type,
                                   id_list,
                                   id_limit=AUTOTASK_API_QUERY_ID_LIMIT,
                                   query_function=get_id_query):
    queries = yield_queries_for_entities_by_id(entity_type, 
                                               id_list, 
                                               id_limit, 
                                               query_function)
    return list(queries)


def yield_queries_for_entities_by_id(entity_type,
                                   id_list,
                                   id_limit=AUTOTASK_API_QUERY_ID_LIMIT,
                                   query_function=get_id_query):
    query_ids = []
    for _id in id_list:
        if len(query_ids) == id_limit:
            yield query_function(entity_type, query_ids)
            query_ids = []
        else:
            query_ids.append(_id)
    if query_ids:
        yield query_function(entity_type, query_ids)


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
    
    get_all_entities = None


    def FROM(self,entity_type):
        self.entity_type = entity_type

        
    def WHERE(self,field_name,field_condition,field_value,udf=False):
        self._add_field(None, field_name, field_condition, field_value, udf)

    
    def OR(self,field_name,field_condition,field_value,udf=False):
        self._add_field('OR', field_name, field_condition, field_value, udf)
    
    
    def AND(self,field_name,field_condition,field_value,udf=False):
        self._add_field('AND', field_name, field_condition, field_value, udf)
        
        
    def open_bracket(self,operator=None):
        attrib = {}
        if operator:
            attrib = {'operator':operator}
        self._cursor = SubElement(self._cursor,'condition',attrib=attrib)
    
    
    def close_bracket(self):
        self._close_cursor()
        

    def reset(self):
        self._query_elements = []
        self._query_elements.append(self._query)
        self._query.clear()
        self.minimum_id_xml = None
        self.minimum_id = None
        self.minimum_id_field = 'id'

    
    def get_query_xml(self):
        self._entityxml.text = self.entity_type
        if self.minimum_id:
            self._add_min_id_field()
        query_xml = tostring(self._queryxml, encoding=QUERY_ENCODING)
        #query_xml = query_xml.encode('utf-8')
        return query_xml
    
    
    def pretty_print(self):
        import xml.dom.minidom
        return xml.dom.minidom.parseString(self.get_query_xml()).toprettyxml()
    
    
    def set_minimum_id(self,minimum_id,field='id'):
        self.minimum_id = minimum_id
        self.minimum_id_field = field
        

    @property
    def _cursor(self):
        return self._query_elements[-1]
    
    
    @_cursor.setter
    def _cursor(self, element):
        self._query_elements.append(element)
        
        
    def _close_cursor(self):
        del(self._query_elements[-1])
        

    def _add_field(self,operator,field_name,field_condition,field_value,udf=False):
        attributes = {}
        if udf:
            attributes['udf'] = 'true'
        if operator:
            self.open_bracket(operator)
        field = SubElement(self._cursor,'field', attrib=attributes)
        field.text = field_name
        expression = SubElement(field,'expression',attrib={'op':field_condition})
        expression.text = self._process_field_value(field_value)
        if operator:
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
        # use _add_field instead of self.AND because we need to keep the
        # expression
        expression = self._add_field('AND',
                                     self.minimum_id_field,
                                     self.GreaterThan,
                                     minimum_id)[1]
        self.minimum_id_xml = expression
    
    
    def _process_field_value(self,value):
        if type(value) is datetime:
            return format_datetime_for_api_query(value)
        return query_escape(str(value))
    
    
    def __init__(self,entity_type = None):
        self.get_all_entities = WRAPPER_DEFAULT_GET_ALL_ENTITIES
        self.entity_type = entity_type
        self._queryxml = Element('queryxml')
        self._entityxml = SubElement(self._queryxml, 'entity')
        self._query = SubElement(self._queryxml, 'query')
        self.reset()


    def __str__(self):
        return repr(self.get_query_xml())
    