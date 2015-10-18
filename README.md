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
Quickstart
---
This is a sample script showing a simple use case.

First, generate a picklist module for your project.
This will create a file for import that contains picklists from Autotask.
It's useful for moving between development and live
It needs updating any time a picklist changes in Autotask.
atws_create_picklist <username> <password> <target_file>

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
print query.get_query_xml()


at = atws.connect(username='<username>', password='<password>')
# tickets is now populated with all the results possible from the above
# query - so it could be 2150 tickets (or more), which would have been 5 API calls.
tickets = at.query(query)

tickets_to_update = []
for ticket in tickets:
	if ticket.IssueType != atvar.Ticket_IssueType_NonWorkIssues:
		ticket.Status = atvar.Ticket_Status_FollowUpRequired
		tickets_to_update.append(ticket)
# if there were 670 tickets to update, this would have been 
# either 670 API calls if the tickets have UDF fields
# or 4 API calls
updated_tickets = at.update(tickets_to_update)

# make an API call for every ticket that is a Non Work Issue
for ticket in tickets:
	if ticket.IssueType == atvar.Ticket_IssueType_NonWorkIssues:
		ticket.Status = atvar.Ticket_Status_Complete
		# update the ticket right now with an API call
		ticket.update()





```
Wrapper


