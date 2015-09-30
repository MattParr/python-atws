'''
Created on 27 Sep 2015

@author: matt
'''
import logging
import atws
from atws.connection import get_zone_url
from atws.connection import connect
from suds.cache import ObjectCache

from passwords import password,username

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

atws.connection.REQUEST_TRANSPORT_TYPE = False
atws.connection.REQUEST_TRANSPORT_TYPE = True



print get_zone_url(username)

# suds plugins example... not required
oc = ObjectCache()
oc.duration = 3600
at = connect(username=username,password=password,cache=oc)

version = at.GetWsdlVersion() 
print version


# tested using notes on a specific ticket to make my life easy
ticket 377506


quit()