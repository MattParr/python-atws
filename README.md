Autotask Web Services (atws)
===
Features
---
* very easy query writing
* picklist generator
* timestamp conversions are handled inbound and outbound
* returns entities with crud (create, reload, update, delete)
* easier UDF setting/getting (get_udf, set_udf)
* monkey patch your entities to add features you need

Installation
---
The following command should allow pip to download the suds-jurko package from the mercurial repo on bitbucket.
You will need the mercurial clients. (yum install mercurial)
```
pip install --extra-index-url https://testpypi.python.org/pypi 	--process-dependency-links --allow-external suds --trusted-host bitbucket.org atws==0.1.dev12
```

Quickstart
---
This is a sample script showing a simple use case.

First, generate a picklist module for your project.
This will create a file for import that contains picklists from Autotask.
It's useful for moving between development and live, and it also allows for constants completion in your IDE.
It needs updating any time a picklist changes in Autotask.
```
create_picklist_module.py <username> <password> <target_file>
```

Example Usage
----
```python
import atws
import atws_picklists_dev as atvar
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
query = atws.Query('Tickets')
query.WHERE('id',query.GreaterThan,5667)
query.Bracket('AND')
query.OR('Status',query.Equals,atvar.Ticket_Status_Complete)
query.OR('IssueType',query.Equals,atvar.Ticket_IssueType_NonWorkIssues)
query.CloseBracket()
# in ATWS XML, it would look like this
print query.pretty_print()

at = atws.connect(username='<username>', password='<password>')
# at.query returns a generator which will return tickets
# in batches of 200 until all the results possible from the above
# query have been retrieved - so it could be 2150 tickets (or more), 
# which would have been 5 API calls.
tickets = at.query(query).fetch_all()

tickets_to_update = []
for ticket in tickets:
	if ticket.IssueType != atvar.Ticket_IssueType_NonWorkIssues:
		ticket.Status = atvar.Ticket_Status_FollowUpRequired
		tickets_to_update.append(ticket)
# if there were 670 tickets to update, this would have been 
# either 670 API calls if the tickets have UDF fields
# or 4 API calls
update_cursor = at.update(tickets_to_update)
# this is a generator, so updates are not performed until 
# you cycle through the results
for ticket in response:
	print ticket.id
#or you can get the results:
updated_tickets = update_cursor.fetch_all()
#or you can just do the update and discard the results
update_cursor.execute()


# this is very useful when you have something like this
query = Query('Ticket')
query.WHERE('id',query.GreaterThan,0) # this would be > 800000 ticket on our system.

query_cursor = at.query(query_results)

def unassign(tickets):
	for ticket in tickets:
		ticket.PrimaryResourceID = ''
		yield ticket

modified_tickets = unassign(query_cursor)
update_cursor = at.update( modified_tickets )
# at this point, nothing has happened yet.

# now we iterate over the generator, querying tickets 500 at a time
# and updating tickets 200 at a time
update_cursor.execute()

# at any given time, there are not more than 500 tickets in memory.
# but we process over 800000 tickets.



# make an API call for every ticket that is a Non Work Issue
# by using the update method from within the entity
for ticket in tickets:
	if ticket.IssueType == atvar.Ticket_IssueType_NonWorkIssues:
		ticket.Status = atvar.Ticket_Status_Complete
		# update the ticket right now with an API call
		ticket.update()

# creating an entity using the create method and auto filling
# the entity during create
ticket = at.new('Ticket',{'Status':atvar.Ticket_IssueType_NonWorkIssues,
                          'QueueID':atvar.Ticket_Queue_Standard,
                          'and so on':'for other fields'})
ticket.create()
print ticket.id



```


