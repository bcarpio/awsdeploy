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
    
def puppet_node_info(region,node):
    puppet_config = config.puppet_enc(region)
    database = puppet_config['database']
    collection = puppet_config['collection']
    host = puppet_config['host']
    con = Connection(host)
    col = con[database][collection]
    node = col.find_one({'node' : node})
    return node

def puppet_node_update_classes(region,node,classes):
    puppet_config = config.puppet_enc(region)
    database = puppet_config['database']
    collection = puppet_config['collection']
    host = puppet_config['host']
    con = Connection(host)
    col = con[database][collection]
    host = col.find_one({ 'node' : node})
    if host == None:
        print "ERROR: Not Node In Mongo ENC. Please Use -a new"
        sys.exit(1)
    c = {}
    for pclass in classes:
        c[pclass] = ''
    col.update({ 'node' : node }, { '$set': { 'enc.classes' : c }})
