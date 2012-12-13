#!/usr/bin/python
# vim: set expandtab:
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from awsdeploy import config
from pymongo import Connection

def puppet_enc(region):
    puppet_config = config.puppet_enc(region)
    database = puppet_config['database']
    collection = puppet_config['collection']
    host = puppet_config['host']
    con = Connection(host)
    col = con[database][collection]
    nodes = col.find()
    return nodes
    
