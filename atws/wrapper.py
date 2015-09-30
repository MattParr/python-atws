'''
Created on 27 Sep 2015

@author: matt
'''
import logging
import math
from constants import AUTOTASK_API_ENTITY_SEND_LIMIT,WRAPPER_DISABLE_CLEAN_ENTITIES
from helpers import can_multiupdate_entities,clean_entities,split_entities_into_packet_lengths
from connection import Connection

logger = logging.getLogger(__name__)

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
        if action not in ('create','update','delete'):
            raise Exception('action not in create update delete: {}'.format(action))
        
        entities = list(entities)
        if not entities:
            raise Exception('process entities called without anything in the entity list')

        if not WRAPPER_DISABLE_CLEAN_ENTITIES:
            clean_entities(entities)
        
        multiupdate = kwargs.get('bulksend',None)
        if multiupdate == True:
            packet_limit = kwargs.get('packet_limit',AUTOTASK_API_ENTITY_SEND_LIMIT)
        elif multiupdate == False:
            packet_limit = 1
        elif can_multiupdate_entities(entities):
            packet_limit = AUTOTASK_API_ENTITY_SEND_LIMIT
        else:
            packet_limit = 1

        packet_lists = split_entities_into_packet_lengths(entities,packet_limit)
        packets = [self.get_entity_packet(packet_list) for packet_list in packet_lists]
        
        results = []
        for packet in packets:
            try:
                results.append(self._send_packet(action,packet))
            except Exception:
                raise AutotaskProcessException(results)

    
    def _get_entity_packet(self,entities):
        packet = self.client.factory.create('ArrayOfEntity')
        packet.Entity = entities
        return packet
        
    
    def _send_packet(self,action,packet):
        return getattr(self.client.service,action)(packet)
    