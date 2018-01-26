'''
Created on 27 Sep 2015

@author: matt

'''
from __future__ import absolute_import
from future.utils import iteritems
import os
import logging
import re
import time
from datetime import datetime
from uuid import uuid4
from .constants import (MONKEY_PATCHING_ENABLED,
                        WRAPPER_DISABLE_CLEAN_ENTITIES,
                        AUTOTASK_API_ENTITY_SEND_LIMIT)
from .helpers import (get_result_entities,
                      datetime_to_api_timezone_entity,
                      trim_empty_strings_entity,
                      datetime_to_local_timezone_entity,
                      get_field_info,
                      clean_entity,
                      process_entity,
                      query_requires_another_call,
                      get_highest_id,
                      get_entity_type,
                      trim_single_space_strings_entity)
from . import monkeypatch
from .monkeypatch import crud
from .monkeypatch import userdefinedfields
from . import connection
from .picklist import Picklists
from suds import sudsobject, MethodNotFound
from suds.plugin import MessagePlugin


logger = logging.getLogger(__name__)


def connect(**kwargs):
    if 'support_files_path' in kwargs:
        plugin = SupportFilesPlugin(kwargs['support_files_path'])
        client_options = kwargs.setdefault('client_options', {})
        plugins = client_options.setdefault('plugins', [])
        plugins.append(plugin)
    wrapper = connection.connect(atws_version=Wrapper,**kwargs)
    if MONKEY_PATCHING_ENABLED:
        monkeypatch.monkey_patch(wrapper)

    return wrapper 


def enable_support_files(path = None):
    raise DeprecationWarning('This is no longer used. use...:'
                             '''connect(support_files_path=<path to dir>)''')
    

class SupportFilesPlugin(MessagePlugin):
    '''
    creates files for sending to autotask
    set the variables:
    constants.SUPPORT_FILES_ENABLED = True
    constants.SUPPORT_FILES_LOCATION = 'path to save files'
    '''
    def __init__(self, support_files_path):
        self.support_files_path = support_files_path
        
        
    def sending(self, context):
        self.write_file(context.envelope, 'sent')

            
    def received(self, context):
        self.write_file(context.reply, 'received')
    
    
    def write_file(self, output, direction):
        file_name = self._get_file_name(direction)
        with open(file_name, "w") as f:
            logger.info('writing %s xml to %s.xml', direction, file_name)
            f.write(str(output))
            
    
    def _get_file_name(self, direction):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        uuid = uuid4().hex
        file_name = '{}-{}-{}.xml'.format(timestamp, uuid, direction)
        return os.path.join(self.support_files_path, 
                            file_name)


class AutotaskAPIException(Exception):
    message = """Autotask API has returned an error.
    Please process the response attribute in this exception to determine
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
        logger.error(error)
        self.errors.append(error)


    def add_entities(self,entities):
        self.response_count.append(len(entities))
        self._wrapper.process_inbound_entities(entities)
        return entities
            

    def raise_or_return_entities(self):
        if self.errors:
            self._raise()
    
    
    def _raise(self):
        raise AutotaskAPIException(self)
    
    
    def __init__(self,wrapper):
        self._wrapper = wrapper
        self.response_count = []
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
            return self._record_successful_entities(result)
        else:
            return self._record_failure(result,packet.Entity)


    def _record_successful_entities(self,result):
        entities = get_result_entities(result)
        return self.add_entities(entities)        

    
    def _record_failure(self,result,entities):
        successful_entities = self._record_successful_entities(result)
        errors = [self._get_error(error,entities) for error in self._get_errors(result)]
        self.add_error({'errors':errors,
                            'packet':entities})
        return successful_entities
        

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
            return self.add_entities(get_result_entities(result))
        else:
            self._add_errors(self._get_errors(result),query)
        logger.debug('Adding successful result number:%s to query response',
                        len(self.response_count)
                     )
        return []
    
    def _add_errors(self,errors,query):
        for error in errors:
            self.add_error(error.Message)
        self.add_error(query.get_query_xml())


class Cursor(object):
    def __init__(self,generator):
        self._generator = generator
        
    
    def __iter__(self):
        'Returns itself as an iterator object'
        return self._generator
    
    
    def __getattr__(self,attr):
        return getattr(self._generator,attr)
    

class QueryCursor(Cursor):
    def fetch_all(self):
        return list(self._generator)    
    
    
    def fetch_one(self):
        return next(self._generator,None)
    
    
class ActionCursor(QueryCursor):
    def execute(self):
        for _ in self._generator:
            pass
    
        
class Wrapper(connection.Connection):
    outbound_entity_functions = [datetime_to_api_timezone_entity, 
                                 trim_empty_strings_entity]
    inbound_entity_functions = [datetime_to_local_timezone_entity,
                                trim_single_space_strings_entity]
    
    
    @property
    def picklist(self):
        try:
            picklist = self._picklist
        except MethodNotFound:
            picklist = Picklists(self)
            self._picklist = picklist
        return picklist
        
        
    def new(self,entity_type,**kwargs):
        entity = self.client.factory.create(entity_type)
        for k,v in iteritems(kwargs):
            setattr(entity,k,v)
        return entity


    def get_field_info(self,entity_type):
        return get_field_info(self, entity_type)


    def get_udf_info(self,entity_type):
        fields = self.client.factory.create('getUDFInfo')
        fields.psTable = entity_type
        return self.client.service.getUDFInfo(fields)

    
    def create(self,entities,**kwargs):
        return ActionCursor(self.process(entities,'create',**kwargs))


    def update(self,entities,**kwargs):
        return ActionCursor(self.process(entities,'update',**kwargs))

    
    def delete(self,entities,**kwargs):
        return ActionCursor(self.process(entities,'delete',**kwargs))    


    def process(self,entities,action,**kwargs):
        if isinstance(entities, sudsobject.Object):
            entities = [entities]
        if not entities:
            raise Exception('process entities called without anything in the entity list')
        if action not in ('create','update','delete'):
            raise Exception('action not in create update delete: {}'.format(action))
        response = ResponseAction(self)
        packet_entities = []
        packet_limit = self._get_packet_limit(**kwargs)
        for entity in entities:
            self._process_outbound_entity(entity)
            if len(packet_entities) != packet_limit:
                packet_entities.append(entity)
                continue
            packet = self._get_entity_packet(packet_entities)
            for returned_entity in self._send_packet(action, packet, response):
                yield returned_entity
            packet_entities = [entity]
        if packet_entities:
            packet = self._get_entity_packet(packet_entities)
            for returned_entity in self._send_packet(action, packet, response):
                yield returned_entity
        response.raise_or_return_entities()


    def process_inbound_entities(self,entities):
        for entity in entities:
            self._process_inbound_entity(entity)
        

    def query(self,query):
        response = ResponseQuery(self)
        return QueryCursor(self._query(query,response))


    def queries(self,queries):
        response = ResponseQuery(self)
        return QueryCursor(self._queries(queries, response))
        

    def _process_outbound_entity(self,entity):
        if not WRAPPER_DISABLE_CLEAN_ENTITIES:
            clean_entity(entity)
        process_entity(entity, self.outbound_entity_functions)


    def _process_inbound_entity(self,entity):
        process_entity(entity, self.inbound_entity_functions)


    def _query(self,query,response,**kwargs):
        finished = False
        while not finished:
            try:
                xml = query.get_query_xml()
            except AttributeError:
                xml = query            
            try:
                logger.debug('fetching query results %s/? for %s',
                             len(response.response_count) + 1,
                             query.entity_type)
                result = self.client.service.query(xml)
                logger.debug('fetched query results')
            except Exception as e:
                raise AutotaskProcessException(e,response)
            else:
                for entity in response.add_result(result, query):
                    yield entity
            if query_requires_another_call(result, query):
                highest_id = get_highest_id(result,query.minimum_id_field)
                query.set_minimum_id(highest_id)
            else:
                finished = True
        if not kwargs.get('queries',False):
            response.raise_or_return_entities()
    
    
    def _queries(self,queries,response):
        for query in queries:
            for entity in self._query(query, response, queries=True):
                    yield entity
        response.raise_or_return_entities()
    

    def _get_packet_limit(self,**kwargs):
        multiupdate = kwargs.get('bulksend',None)
        if multiupdate == False:
            return 1
        else:
            return kwargs.get('packet_limit',
                              AUTOTASK_API_ENTITY_SEND_LIMIT)
        
    
    def _get_entity_packet(self,entities):
        packet = self.client.factory.create('ArrayOfEntity')
        packet.Entity = entities
        return packet
        

    def _send_packet(self,action,packet,response):
        logger.debug('%s packet containing %s %s',
                     action,
                     len(packet.Entity),
                     get_entity_type(packet.Entity[0]))
        try:
            result = getattr(self.client.service,action)(packet)
        except Exception as e:
            # @todo the failed packet needs to come in here
            # to be available in the response exception
            logger.exception('An unhandled exception in the wrapper.')
            raise AutotaskProcessException(e,response)
        else:
            logger.debug('yielding packet response')
            return response.add_result(result, packet)

