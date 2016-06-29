# -*- coding: utf-8 -*-
import click
import os
import argparse
import atws
from atws.helpers import create_atvar_module
from atws.monkeypatch.duckpunch import BLACKLISTED_TYPES, get_api_types

@click.command()
def main(args=None):
    parser = argparse.ArgumentParser(description='test')
    parser.add_argument('target_path')
    parser.add_argument('--username', 
                        default=os.environ.get('AUTOTASK_API_USERNAME', None))
    parser.add_argument('--password', 
                        default=os.environ.get('AUTOTASK_API_PASSWORD', None))
    parser.add_argument('--url', 
                        default=os.environ.get('AUTOTASK_API_URL', None))
    parser.add_argument('--entities',
                        help='Space delimited entity types for inclusion',
                        nargs='+', 
                        default=[]
                        )
    
    args = parser.parse_args()
    if not args.username or not args.password:
        exit(parser.print_usage())
    
    at = atws.connect(url=args.url,
                      username=args.username,
                      password=args.password)
    
    if args.entities:
        entities = args.entities
    else:
        entities = get_api_types(at.client, BLACKLISTED_TYPES)
    
    create_atvar_module(at, entities, args.target_path)


if __name__ == "__main__":
    main()