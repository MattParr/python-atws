=====
Usage
=====

To use Python AutoTask Web Services  in a project::

    import atws

To enable some of the additional features that process over every entity 
returned by a query, the module must be imported explicitly so that it can
monkeypunch the suds library.  CRUD and UserdefinedFields are imported by the
wrapper by default, but the others are not enabled by default.::

    import atws.monkeypunch.attributes
    

Connecting to Autotask
----------------------

Only a username and password are required, but if you are initialising the 
library often, it may pay to also include the zone url, otherwise it needs to 
be discovered by performing an API lookup.::

    at = atws.connect(username='user@usernamespace.com',password='userpassword')
    

Picklist module
---------------

There is a shell script installed that will create a python module that 
contains variables with picklist names, and assignments to those variables 
with the picklist ID value.
Usage: create_picklist_module [OPTIONS] TARGET_PATH::

    $ create_picklist_module --username 'user@usernamespace.com' \
    --password 'userpassword' atvar.py
    
    
And then you have a python module::

    import atvar.py
    print atvar.TicketStatusComplete
    5
    
    
Querying for entities
---------------------

The Query object::

    ''' In SQL this query would be:
    SELECT * FROM tickets WHERE 
    id > 5667
    AND 
    (
     Status = 'Complete'
     OR
     IssueType = 'Non Work Issues'
    )
    '''
    query = atws.Query('Ticket')
    query.WHERE('id',query.GreaterThan,5667)
    query.Bracket('AND')
    query.OR('Status',query.Equals,atvar.Ticket_Status_Complete)
    query.OR('IssueType',query.Equals,atvar.Ticket_IssueType_NonWorkIssues)
    query.CloseBracket()
    # in ATWS XML, it would look like this
    print query.pretty_print()


Query result cursor
-------------------

The query method in the wrapper accepts the query, and returns a generator
cursor which can be used to enumerate the results::

    tickets = at.query(query)
    # enumerate them
    for ticket in tickets:
        do_something(ticket)
        
    # process them like a generator
    ticket = ticket.next()
    
    # or get a list
    all_tickets = at.query(query).fetch_all()
    
    # or if you know you are just getting one result
    ticket = at.query(query).fetch_one()
    
    
Updating entities
-----------------

Following on from the previous query result example... entities can be modified,
and then returned to the API.  It's best to do this using a generator function 
so that you can process in batches of 500 and 200.  The Autotask API only gets
a maximum of 500 entities per query, and can only submit 200 entities to be 
processed.::
    
    
    def close_tickets(tickets):
        for ticket in tickets:
            ticket.Status = atvar.TicketStatusComplete
            yield ticket
            
    
    tickets = at.query(query)
    # still nothing has been done
    tickets_to_update = close_tickets(tickets)
    # a generator cursor result again - still nothing has been done
    updated_tickets = at.update(tickets_to_update)
    
    # now the query is executed
    # and then the entities are modified and resubmitted for processing
    for ticket in updated_tickets:
        print ticket.id, 'was closed'
        
    # if there were 1400 tickets in the results, then the following activity 
    # would take place:
    # query #1 returns ticket ids 1-500
    # ticket ids 1-200 are submitted for processing
    # ticket ids 201-400 are submitted for processing
    # query #2 returns ticket ids 501-1000
    # ticket ids 401-600 are submitted for processing
    ##.... 
    
    # if you don't need to see the results, you can just:
    at.update(tickets_to_update).execute()
    

Creating entities
-----------------

To create an entity, you must first create the object, and then submit it to 
be processed.::

    new_ticket = at.new('Ticket')
    new_ticket.Title = 'This title'
    new_ticket.Description = 'This description'
    
    # if you are just submitting one ticket...
    ticket = at.create(new_ticket).fetch_one()
    
    # if you are submitting many tickets, then you have the same querycursor
    # options.  Process in submissions of 200 entities per API call:
    tickets = at.create(new_tickets)
    # or process them all at once:
    tickets = at.create(new_tickets).fetch_all()
    # or process them without keeping the results:
    tickets = at.create(new_tickets).execute()
    

CRUD
----

CRUD feature to the suds objects returned in the wrapper.
It supports Create, Update, Refresh, and Delete::

    ticket = at.new('Ticket')
    ticket.Title = 'Test ticket - no id yet'
    assert hasattr(ticket, 'id') is False
    ticket.create() # this will create the ticket in Autotask
    assert ticket.id
    
    ticket.Title = 'I changed this'
    ticket.update() # this will update the ticket in Autotask


Userdefined Fields
------------------

Userdefined Fields are a little odd in the default suds object, so they are 
wrapped to provide a better interface to handle them.::

    my_udf_value = ticket.get_udf('My Udf Name')
    
    ticket.set_udf('My Udf Name', my_new_udf_value)
    ticket.update()
    
    # coming in version 0.2.1
    # all attributes can be accessed by index
    ticket_status = ticket['Status']
    # if the attribute is missing, UDF will be presumed
    my_udf_value = ticket['My Udf Name']
    # and likewise for assignment.  if the attribute to be assigned isn't in the 
    SOAP specification, then a UDF will be assumed.
    ticket['Status'] = atvar.TicketStatusComplete
    ticket['My New Userdefined Field'] = my_udf_value
    ticket.update()
    

Additional Features
-------------------


Attributes
~~~~~~~~~~


Marshallable
~~~~~~~~~~~~


AsDict
~~~~~~


Advanced Example
----------------


