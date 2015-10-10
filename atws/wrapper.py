'''
Created on 27 Sep 2015

@author: matt

@todo: - a generic entity monkey patch plugin
@todo: - a way of adding a custom patch to the monkey patching
@todo: - a picklist object.  pass entity,field and AT connection.  translates from API return to picklist Value
@todo: - a switch to turn on picklist and monkey patch the values in on return eg:ticket.IssueTypeName becomes the name value
@todo: - a switch to turn on full object resolution.  So a ticket would come back with all the possible entities 
        eg: it would have ticket.Contact would be a contact object.  ticket.Account would be the account Object
        - it would take all the results of the query, then get all the required contacts in one call etc.
'''
import logging
import re
from constants import *
from helpers import *
import connection
from connection import Connection
from suds import sudsobject


logger = logging.getLogger(__name__)


def connect(**kwargs):
    wrapper = connection.connect(atws_version=Wrapper,**kwargs)
    if MONKEY_PATCHING_ENABLED:
        from monkey_patch import MonkeyPatch
        MonkeyPatch(wrapper,**kwargs)
    return wrapper 


class AutotaskAPIException(Exception):
    message = """Autotask API has returned an error.
    Please process the response attribute in this exception to detirmine 
    the extent of this failure.
    """ 
    
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return repr(self.message) + repr(self.response.errors)          


class AutotaskProcessException(Exception):
    message = """During send or receive with the API, an error has 
    occurred.  Please see the exception attribute for details about the error.
    Please see the response attribute as some API commands may have sucessfully 
    completed before the exception occurred
    """
    
    def __init__(self, exception, response):
        self.exception = exception
        self.response = response
    
    
    def __str__(self):
        return repr(self.message) + repr(self.exception) + repr(self.response.errors)
    
    
class Response(object):
    
    def add_error(self,error):
        self.errors.append(error)


    def add_entities(self,entities):
        try:
            self.successful_entities.extend(entities)
        except TypeError:
            self.successful_entities.append(entities)
            

    def raise_or_return_entities(self):
        if self.errors:
            self._raise()
        else:
            return self.successful_entities
    
    
    def _raise(self):
        raise AutotaskAPIException(self)
    
    
    def __init__(self):
        self.errors = []
        self.successful_entities = []
        self.failed_entities = []    

        
    def _get_errors(self,result):
        try:
            return result.Errors.ATWSError
        except Exception:
            return []    
    
    
class ResponseAction(Response):
    
    def add_result(self,result,packet):
        if result.ReturnCode == 1:
            self._record_success(result)
        else:
            self._record_failure(result,packet.Entity)


    def _record_success(self,result):
        self._record_successful_entities(result)


    def _record_successful_entities(self,result):
        entities = get_result_entities(result)
        self.add_entities(entities)        

    
    def _record_failure(self,result,entities):
        self._record_successful_entities(result)
        errors = [self._get_error(error,entities) for error in self._get_errors(result)]
        self.add_error({'errors':errors,
                            'packet':entities})
        

    def _get_errored_entity_index(self,message):
        if "Error updating entity for record number" in message:
            matched = re.findall(r'\[(.*)\]', message)
            if matched:
                return int(matched[0])-1
        return None
    
    
    def _get_failed_entity(self,error,entities):
        errorKey = self._get_errored_entity_index(error.Message)
        if errorKey:
            entity = entities[errorKey]
            self.failed_entities.append(entity)
            return [entity]
        self.failed_entities.extend(entities)
        return entities


    def _get_error(self,error,entities):
        failed_entities = self._get_failed_entity(error, entities)
        return {'message':error.Message,
                'failed_entities':failed_entities}
            

class ResponseQuery(Response):
    def add_result(self,result,query):
        if result.ReturnCode == 1:
            self.add_entities(get_result_entities(result))
        else:
            self._add_errors(self._get_errors(result),query)
    
    
    def _add_errors(self,errors,query):
        for error in errors:
            self.add_error(error.Message)
        self.add_error(query.get_query_xml())
    
        
class Wrapper(Connection):
    
    def new(self,entity_type):
        return self.client.factory.create(entity_type)
    
    
    def get_field_info(self,entity_type):
        fields = self.client.factory.create('GetFieldInfo')
        fields.psObjectType = entity_type
        return self.client.service.GetFieldInfo(fields)


    def get_udf_info(self,entity_type):
        fields = self.client.factory.create('getUDFInfo')
        fields.psTable = entity_type
        return self.client.service.getUDFInfo(fields)

    
    def create(self,entities,**kwargs):
        return self.process(entities,'create',**kwargs)


    def update(self,entities,**kwargs):
        return self.process(entities,'create',**kwargs)

    
    def delete(self,entities,**kwargs):
        return self.process(entities,'create',**kwargs)    


    def process(self,entities,action,**kwargs):
        if isinstance(entities, sudsobject.Object):
            entities = [entities]
        if not entities:
            raise Exception('process entities called without anything in the entity list')
        if action not in ('create','update','delete'):
            raise Exception('action not in create update delete: {}'.format(action))
        if not WRAPPER_DISABLE_CLEAN_ENTITIES:
            clean_entities(entities)
        
        packet_limit = self._get_packet_limit(entities,**kwargs)
        packet_lists = split_list_into_chunks(entities,packet_limit)
        packets = [self._get_entity_packet(packet_list) for packet_list in packet_lists]
        
        response = ResponseAction()
        for packet in packets:
            try:
                result = self._send_packet(action,packet)
            except Exception as e:
                # @todo the failed packet needs to come in here
                # @todo upstream in the transport - should handle retries
                # for ssl handshake timeouts etc (transient error retries)
                raise AutotaskProcessException(e,response)
            response.add_result(result, packet)
        return response.raise_or_return_entities()


    def query(self,query):
        response = ResponseQuery()
        finished = False
        while not finished:
            try:
                xml = query.get_query_xml()
            except AttributeError:
                xml = query            
            try:
                result = self.client.service.query(xml)
                response.add_result(result, query)
            except Exception as e:
                raise AutotaskProcessException(e,response)
            if query_requires_another_call(result, query):
                highest_id = get_highest_id(result,query.minimum_id_field)
                query.set_minimum_id(highest_id)
            else:
                finished = True
        return response.raise_or_return_entities()


    def _get_packet_limit(self,entities,**kwargs):
        multiupdate = kwargs.get('bulksend',None)
        if multiupdate == True:
            return kwargs.get('packet_limit',AUTOTASK_API_ENTITY_SEND_LIMIT)
        if multiupdate == False:
            return 1
        if can_multiupdate_entities(entities):
            return AUTOTASK_API_ENTITY_SEND_LIMIT
        return 1        
        
    
    def _get_entity_packet(self,entities):
        packet = self.client.factory.create('ArrayOfEntity')
        packet.Entity = entities
        return packet
        

    def _send_packet(self,action,packet):
        return getattr(self.client.service,action)(packet)
    