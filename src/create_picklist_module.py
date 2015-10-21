#!/bin/env python
import atws
import os
import argparse
import re
from atws.helpers import get_picklist_stream,get_picklists, get_field_info
from atws.monkeypatch.duckpunch import BLACKLISTED_TYPES, get_api_types
from suds import WebFault

csnregex = re.compile('^\d+$')

def main():
        
    parser = argparse.ArgumentParser(description='test')
    parser.add_argument('target_path')
    parser.add_argument('--username', default=os.environ.get('AUTOTASK_API_USERNAME', None))
    parser.add_argument('--password', default=os.environ.get('AUTOTASK_API_PASSWORD', None))
    parser.add_argument('--url', default=os.environ.get('AUTOTASK_API_URL', None))
    parser.add_argument('--entities',
                        help='Space delimited list of entity types for inclusion',
                        nargs='+', 
                        default=[]
                        )
    
    args = parser.parse_args()
    if not args.username or not args.password:
        exit(parser.print_usage())
    
    at = atws.connect(url=args.url,username=args.username,password=args.password)
    
    if args.entities:
        entities = args.entities
    else:
        entities = get_api_types(at.client, BLACKLISTED_TYPES)
    
    a = open(args.target_path,"w")
    for entity_type in entities:
        try:
            field_info_response = get_field_info(at,entity_type)
        except WebFault:
            pass
        else:
            picklists = get_picklists(field_info_response)
            for line in get_picklist_stream(entity_type,picklists):
                a.write( line )


if __name__ == '__main__':
    main()