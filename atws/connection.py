'''
Created on 27 Sep 2015

@author: matt
'''
from __future__ import absolute_import
from builtins import range
import logging
import suds.client
import suds.transport as transport
from .constants import (REQUEST_TRANSPORT_TRANSIENT_ERROR_RETRIES,
                        REQUEST_TRANSPORT_TIMEOUT_CONNECT_WAIT,
                        REQUEST_TRANSPORT_TIMEOUT_RESPONSE_WAIT,
                        AUTOTASK_API_BASE_URL,
                        DISABLE_SSL_WARNINGS,
                        USE_REQUEST_TRANSPORT_TYPE)
                        
from _ssl import SSLError
from requests.exceptions import ConnectTimeout, Timeout, ReadTimeout

logger = logging.getLogger(__name__)
suds_version = float(suds.__version__[:3])
logger.debug('Suds Version %s', suds_version)

if suds_version < 0.7:
    logger.warning('Suds version (%s) not ideal. Please use 0.7',
                   suds_version)

import requests
import functools
import traceback
try:
    from cStringIO import StringIO 
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import BytesIO as StringIO

MAX_RETRIES = REQUEST_TRANSPORT_TRANSIENT_ERROR_RETRIES

def get_zone_info(username):
    client = suds.client.Client(url=AUTOTASK_API_BASE_URL)
    return client.service.getZoneInfo(username)


def get_zone_url(username):
    zone_info = get_zone_info(username)
    return zone_info.URL


def get_zone_id(username):
    zone_info = get_zone_info(username)
    return zone_info.CI


def get_zone_wsdl(username):
    url = get_zone_url(username)
    try:
        return url.replace('asmx','wsdl')
    except AttributeError:
        logging.exception('failed to resolve zone')
        raise ValueError('Username:{} failed to resolve to a zone'.format(
            username))


def get_connection_url(**kwargs):
    try:
        url = kwargs['url']
        assert url
    except (KeyError, AssertionError):
        url = get_zone_wsdl(kwargs['username'])
    return url

    
def disable_warnings():
    import requests.packages
    requests.packages.urllib3.disable_warnings()
    
    
def connect(**kwargs):
    client_options = kwargs.setdefault('client_options',{})
    if DISABLE_SSL_WARNINGS:
        disable_warnings()
    if USE_REQUEST_TRANSPORT_TYPE:
        session = requests.Session()
        session.auth = (kwargs['username'],kwargs['password'])
        session.mount("http://", 
                      requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES))
        session.mount("https://", 
                      requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES))
        transport = client_options.setdefault('transport',
                                              RequestsTransport(session))
    
    url = get_connection_url(**kwargs)
    client_options['url'] = url
    obj = kwargs.get('atws_version',Connection)
    return obj(**kwargs)


def handle_errors(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.HTTPError as e:
            raise transport.TransportError(
                'Error in requests\n' + traceback.format_exc(),
                e.response.status_code,
            )
        except requests.RequestException:
            raise transport.TransportError(
                'Error in requests\n' + traceback.format_exc(),
                000
            )
    return wrapper


class RequestsTransport(transport.Transport):
    # @todo: handle transient errors by retrying
    # ideally, we should only have to raise on a few errors
    # like destination unreachable, but not timeouts or transport
    # failure eg: SSLError below
    def __init__(self, session=None):
        transport.Transport.__init__(self)
        self._session = session or requests.Session()
        self.timeout = (REQUEST_TRANSPORT_TIMEOUT_CONNECT_WAIT,
                        REQUEST_TRANSPORT_TIMEOUT_RESPONSE_WAIT)
        
        
    @handle_errors
    def open(self, request):
        for attempt in range(1,REQUEST_TRANSPORT_TRANSIENT_ERROR_RETRIES + 1):
            try:
                resp = self._session.get(request.url,timeout=self.timeout)
                break
            except (SSLError, ConnectTimeout, Timeout, ReadTimeout):
                if attempt == REQUEST_TRANSPORT_TRANSIENT_ERROR_RETRIES:
                    raise
                continue
        return StringIO(resp.content)
    
    
    @handle_errors
    def send(self, request):
        for attempt in range(1,REQUEST_TRANSPORT_TRANSIENT_ERROR_RETRIES + 1):
            try:
                resp = self._session.post(
                                          request.url,
                                          data=request.message,
                                          headers=request.headers,
                                          )
                break
            except (SSLError, Timeout):
                if attempt == REQUEST_TRANSPORT_TRANSIENT_ERROR_RETRIES:
                    raise
                continue
        return transport.Reply(
            resp.status_code,
            resp.headers,
            resp.content,
        )


class Connection(object):
    '''
    classdocs
    '''
    def __init__(self, **kwargs):
        '''
        Constructor
        '''
        self.kwargs = kwargs
        try:
            self.client = kwargs['client']
        except KeyError:
            options = kwargs.get('client_options',{})
            self.client = suds.client.Client(**options)
    
    
    def __getattr__(self,attr):
        return getattr(self.client.service,attr)
    
    