- [ ] a switch to turn on picklist and monkey patch the values in on return eg:ticket.IssueTypeName becomes the name value
- [] a switch to turn on full object resolution.  So a ticket would come back with all the possible entities 
        eg: it would have ticket.Contact would be a contact object.  ticket.Account would be the account Object
        - it would take all the results of the query, then get all the required contacts in one call etc.
- [] async and threadpool options
        see toolkit_for_requests - threading options for actions where multiple requests are to be perfomed
        - eg create(400 entities using 1 entity per call might run over 40 times over 10 threads)
        - the results processed by the response object
        - simple switch in the connect module to turn it on or off. (threaded wrapper object?)
- [] a lazy loading picklist attribute for the wrapper