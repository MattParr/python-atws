=======
History
=======
0.4.1 (2016-12-18)
------------------

* currency symbol picklist on currency entity was causing create_picklist_module
to fail to complete.  Currency entity is now excluded from default entity set.


0.4.0 (2016-11-04)
------------------

* at.picklists module added
* picklists module with child field picklists
* support files debug feature (saves XML sent and received)
* query now builds XML closer to the API example documentation
* query supports special chars like @ in condition values


0.3.4 (2016-07-07)
------------------

* Py3 marshallable no longer failing due to unicode conversion


0.3.3 (2016-07-07)
------------------

* Py3 marshallable no longer failing due to basestring comparison


0.3.2 (2016-07-07)
------------------

* Py3 queries no longer failing due to encoding with BOM


0.3.0 (2016-07-06)
------------------

* PyPI install missing requirements "future" fixed


0.2.0 (2016-07-01)
------------------

* Python 3 support


0.1.8 (2016-06-28)
------------------

* First proper release on PyPI.
