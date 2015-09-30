'''
Created on 27 Sep 2015

@author: matt
'''
import logging
import re
from constants import AUTOTASK_API_ENTITY_SEND_LIMIT,WRAPPER_DISABLE_CLEAN_ENTITIES
from helpers import can_multiupdate_entities,clean_entities,split_entities_into_packet_lengths
import connection
from connection import Connection


logger = logging.getLogger(__name__)

def connect(**kwargs):
    connection.connect(atws_version='Wrapper',**kwargs)


class AutotaskAPIException(Exception):
    message = """Autotask API has returned an error.
    Please process the response attribute in this exception to detirmine 
    the extent of this failure""" 
    
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return repr(self.message)          


class AutotaskProcessException(Exception):
    message = """During send or receive with the API, and error has 
    occurred.  Please see the exception attribute for details about the error.
    Please see the response attribute as some API commands may have sucessfully 
    completed before the exception occurred"""
    
    def __init__(self, exception, response):
        self.process_exception = exception
        self.response = response
    
    
    def __str__(self):
        return repr(self.message)
    
    
class Response(object):
    
    def __init__(self):
        self.errors = []
        self.successful_entities = []
        self.failed_entities = []
        
    
    def add_result(self,result,packet):
        if result.ReturnCode == 1:
            self._record_success(result)
        else:
            self._record_failure(result,packet.Entity)
    
    
    def raise_or_return_entities(self):
        if self.errors:
            self._raise()
        else:
            return self.successful_entities
    
    
    def _raise(self):
        raise AutotaskAPIException(self)
    
    
    def _get_result_entities(self,result):
        return result.EntityResults.Entity
    
    
    def _record_success(self,result):
        self._record_successful_entities(result)


    def _recored_successful_entities(self,result):
        entities = self._get_result_entities(result)
        self.successful_entities.extend(entities)        

    
    def _record_failure(self,result,entities):
        self._record_successful_entities(result)
        errors = [self._get_error(error,entities) for error in result.Errors.ATWSError]
        self.errors.append({'errors':errors,
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


        
class Wrapper(Connection):
    
    def get_new_entity(self,entity_type):
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
        if not entities:
            raise Exception('process entities called without anything in the entity list')
        if action not in ('create','update','delete'):
            raise Exception('action not in create update delete: {}'.format(action))
        if not WRAPPER_DISABLE_CLEAN_ENTITIES:
            clean_entities(entities)
        
        packet_limit = self._get_packet_limit(entities,**kwargs)
        packet_lists = split_entities_into_packet_lengths(entities,packet_limit)
        packets = [self.get_entity_packet(packet_list) for packet_list in packet_lists]
        
        response = Response()
        for packet in packets:
            try:
                result = self._send_packet(action,packet)
                response.add_result(result, packet)
            except Exception as e:
                raise AutotaskProcessException(response,e)
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
    