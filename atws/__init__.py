'''
@todo: create a picklist object that allows:
preferrably have the wrapper auto generate these objects if needed
but also allow them to be passed in (from a pickle cache later on)
tp = PickList('Ticket')
tp.Status(5) 
'Complete'
tp.Status('Complete')
5
tp.IssueType('ThisIssue')
23455
'''
from pytz import timezone
from wrapper import connect
from query import Query
ATWS_API_TIMEZONE = timezone('US/Eastern')
ATWS_ENTITY_SEND_LIMIT = 200
ATWS_ENTITY_RECEIVE_LIMIT = 500