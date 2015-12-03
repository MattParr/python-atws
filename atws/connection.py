'''
Created on 27 Sep 2015

@author: matt
'''
import logging
import suds.client
import suds.transport as transport
from constants import *
from _ssl import SSLError

logger = logging.getLogger(__name__)
suds_version = float(suds.__version__[:3])
logger.debug('Suds Version %s', suds_version)

if suds_version < 0.7:
    raise Exception('Suds version not supported {}'.format(suds_version))

import requests
import functools
import traceback
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


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
        raise ValueError('Username:{} failed to resolve to a zone'.format(username))


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
        transport = client_options.setdefault('transport',RequestsTransport(session))
    client_options['url'] = kwargs.get('url',get_zone_wsdl(kwargs['username']))
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
        
        
    @handle_errors
    def open(self, request):
        for attempt in xrange(1,REQUEST_TRANSPORT_TRANSIENT_ERROR_RETRIES + 1):
            try:
                resp = self._session.get(request.url,timeout=(3,27))
                break
            except SSLError:
                if attempt == REQUEST_TRANSPORT_TRANSIENT_ERROR_RETRIES:
                    raise
                continue
        return StringIO.StringIO(resp.content)
    
    
    @handle_errors
    def send(self, request):
        for attempt in xrange(0,6):
            try:
                resp = self._session.post(
                                          request.url,
                                          data=request.message,
                                          headers=request.headers,
                                          )
                break
            except SSLError:
                if attempt == 5:
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
    
    