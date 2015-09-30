from pytz import timezone
from datetime import datetime
from constants import AUTOTASK_API_TIMEZONE,AUTOTASK_API_QUERY_ID_LIMIT


def get_id_query(entity,id_list):
    query = at_query()
    query.setEntity(entity)
    for entity_id in id_list:
        query.OR('id',query.Equals,entity_id)
    return query
    
    
def get_multiple_query_results(at,query_list):
    results = list()
    for query in query_list:
        result = at.getEntityResults(query)
        if result:
            results+=result
    return results


def get_queries_for_entities_by_id(entity,
                                   id_list,
                                   id_limit=AUTOTASK_API_QUERY_ID_LIMIT,
                                   query_function=get_id_query):
    # because we can only do circa 200 lines in a query
    # if we need to check more querys, we need more lines
    query_list = list()
    temp_id_list = list()
    i = 0
    for entity_id in id_list:
        i+=1
        temp_id_list.append(entity_id)
        if i == id_limit:
            # generate the query.  put it in the list
            # clear the list, and start again
            query_list.append(query_function(entity,temp_id_list))
            i = 0
            temp_id_list = list()
    if temp_id_list:
        # append the last query
        query_list.append(query_function(entity,temp_id_list))
    return query_list


class at_query:
    Equals='Equals'
    NotEqual='NotEqual'
    GreaterThan='GreaterThan'
    LessThan='LessThan'
    GreaterThanorEquals='GreaterThanorEquals'
    LessThanOrEquals='LessThanOrEquals'
    BeginsWith='BeginsWith'
    EndsWith='EndsWith'
    Contains='Contains'
    IsNotNull='IsNotNull'
    IsNull='IsNull'
    IsThisDay='IsThisDay'
    Like='Like'
    NotLike='NotLike'
    SoundsLike='SoundsLike'
    apitimezone = timezone(AUTOTASK_API_TIMEZONE)
    querytimezone = timezone(LOCAL_TIME_ZONE)

    def FROM(self,entity):
        self._entity=entity


    def WHERE(self,field_name,field_condition,field_value,udf=False):
        self._addFieldCriteria(field_name, field_condition, field_value,udf)
    
    
    def OR(self,field_name,field_condition,field_value,udf=False):
        self._startNestedCondition('OR')
        self._addFieldCriteria(field_name, field_condition, field_value,udf)
        self._endNestedCondition()
    
    
    def AND(self,field_name,field_condition,field_value,udf=False):
        self._startNestedCondition()
        self._addFieldCriteria(field_name, field_condition, field_value,udf)
        self._endNestedCondition()
    
    
    def openBracket(self,operator='AND'):
        bracket=dict()
        bracket['TYPE']='BRACKET'
        bracket['STATUS']=True
        bracket['OPERATOR']=operator
        
        self._operations.append(bracket)
        
    def closeBracket(self):
        bracket=dict()
        bracket['TYPE']='BRACKET'
        bracket['STATUS']=False
        
        self._operations.append(bracket)

    def andOpenBracket(self):
        self.openBracket()
    
    def orOpenBracket(self):
        self.openBracket('OR')
        
    def reset(self):
        self.__init__()
 
    def __init__(self):
        self._operations=list()
        self._spaces=3
        self._xml=""


    def _addFieldCriteria(self,name,condition,value,udf=False):
        field=dict()
        field['TYPE']='FIELD'
        field['NAME']=name
        field['CONDITION']=condition
        field['VALUE']=value
        field['UDF']=udf
        
        self._operations.append(field)
        

    def _startNestedCondition(self,operator='AND'):
        nest=dict()
        nest['TYPE']='NEST'
        nest['OPERATOR']=operator
        nest['STATUS']=True
        
        self._operations.append(nest)


    def _endNestedCondition(self):
        nest=dict()
        nest['TYPE']='NEST'
        nest['STATUS']=False
        
        self._operations.append(nest)

        
    def getQueryXml(self):
        self._buildXml()
        xml=self._xml
        self._xml=""
        return xml

    
    def _buildXml(self):
        for operation in self._operations:
            getattr(self, '_build{0}'.format(operation['TYPE']))(operation)
    
        qxml=self._xml
        xml="<queryxml>\n <entity>{0}</entity>\n  <query>{1}\n  </query>\n</queryxml>"
        self._xml=xml.format(self._entity,qxml)

        
    def _buildFIELD(self,operation):
        name=operation['NAME']
        condition=operation['CONDITION']
        if type(operation['VALUE']) is datetime:
            value = self.formatDateStamp(operation['VALUE'])
        else:
            value=operation['VALUE']
        udf=operation['UDF']
        fspacer=" " * self._spaces
        espacer=" " * (self._spaces +1)

        if udf is True:
            udf=" udf='true'"
        else:
            udf=""
        
        exml="{0}<expression op='{1}'>{2}</expression>"
        exml=exml.format(espacer,condition,value)
        
        fxml="\n{0}<field{1}>{2}\n{3}\n{4}</field>"
        self._xml+=fxml.format(fspacer,udf,name,exml,fspacer)


    def _buildNEST(self,operation):
        if operation['STATUS'] is False:
            self._spaces -= 1
            cspacer=" " * self._spaces
            self._xml+="\n{0}</condition>".format(cspacer)
            
        else:
            cspacer=" " * self._spaces
            cxml="\n{0}<condition operator='{1}'>"
            
            self._xml+=cxml.format(cspacer,operation['OPERATOR'])
            self._spaces += 1

    
    def _buildBRACKET(self,operation):
        self._buildNEST(operation)  
    
    
    def formatDateStamp(self,objDateTime):
        return self.localiseDateTimeField(objDateTime).strftime("%Y-%m-%d %H:%M:%S")


    def localiseDateTimeField(self,objDateTime):
        if objDateTime.tzinfo is None:
            apiDateTime = self.querytimezone.localize(objDateTime).astimezone(self.apitimezone)
        else:
            apiDateTime = objDateTime.astimezone(self.apitimezone)
        
        return apiDateTime
    
    