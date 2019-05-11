=====
Usage
=====

To use Python AutoTask Web Services  in a project::

    import atws

To enable some of the additional features that process over every entity 
returned by a query, the module must be imported explicitly so that it can
monkeypatch the suds library.  CRUD and UserdefinedFields are imported by the
wrapper by default, but the others are not enabled by default.::

    import atws.monkeypatch.attributes
    

Connecting to Autotask
----------------------
* API v1.5

Only a username and password are required, but if you are initialising the
library often, it may pay to also include the zone url, otherwise it needs to
be discovered by performing an API lookup.::

    at = atws.connect(username='user@usernamespace.com',password='userpassword')


If necessary, include the integration code in the connect parameters.::

    at = atws.connect(username='user@usernamespace.com',
                      password='userpassword',
                      integrationcode='27-char-integration-code')

* API v1.6

Autotask PSA API v1.6 requires an integration code while making the connection.
You must also specify the API version in the connect parameters::

    at = atws.connect(username='user@usernamespace.com',
                      password='userpassword',
                      apiversion=1.6,
                      integrationcode='27-char-integration-code')

Support Files
-------------

Often, Autotask support will ask for the XML that is being sent/received
in order to support a problem.  Sometimes you might like to see this raw
output yourself to check date conversions or entity SAX failures.
There is a support file message plugin to copy XML files to a path you specify
when connecting to the API.::

    at = atws.connect(username='user@usernamespace.com',
                      password='userpassword',
                      support_file_path='/tmp')
    
    
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
    query.open_bracket('AND')
    query.OR('Status',query.Equals,at.picklist['Ticket']['Status']['Complete'])
    query.OR('IssueType',query.Equals,
             at.picklist['Ticket']['IssueType']['Non Work Issues'])
    query.close_bracket()
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
            ticket.Status = at.picklist['Ticket']['Status']['Complete']
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


Picklists
---------

Many entities have picklists to describe possible id values for attributes.
Some common ticket entity picklist values are: Status, Priority, QueueID
Looking up the picklists for an entity is an API call.
There is a caching attribute on the wrapper object for accessing picklists.::

    assert at.picklist['Ticket']['Status']['Complete'] == 5
    assert at.picklist['Ticket']['Status'].reverse_lookup(5) == 'Complete'
         
Some picklists are children of parent picklists.  
In a ticket, Subissue type is a child of 
Issue type.  These are handled differently due to possible naming conflicts.::

    at.picklist['Ticket']['SubIssueType']['Hardware Failure']['Mouse']
    
In the example above, 'Hardware Failure' is an Issue Type, and 'Mouse' is a 
Subissue Type.


Creating entities
-----------------

To create an entity, you must first create the object, and then submit it to 
be processed.  Note that many entities have required fields.::

    ticket = at.new('Ticket')
    ticket.Title = 'test ticket'
    ticket.AccountID = 0
    ticket.DueDateTime = datetime.now()
    ticket.Priority = at.picklist['Ticket']['Priority']['Standard']
    ticket.Status = at.picklist['Ticket']['Status']['New']
    ticket.QueueID = at.picklist['Ticket']['QueueID']['Your Queue Name Here']
    #if you are just submitting one ticket:
    ticket.create() # updates the ticket object inline using CRUD patch
    # or:
    new_ticket = at.create(ticket).fetch_one()
    
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
    
    # all attributes can be accessed by index
    ticket_status = ticket['Status']
    # if the attribute is missing, UDF will be presumed
    my_udf_value = ticket['My Udf Name']
    # and likewise for assignment.  if the attribute to be assigned isn't in the 
    SOAP specification, then a UDF will be assumed.
    ticket['Status'] = at.picklist['Ticket']['Status']['Complete']
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


