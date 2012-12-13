#!/usr/bin/python
# vim: set expandtab:
import sys
sys.path.append('../')
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
    