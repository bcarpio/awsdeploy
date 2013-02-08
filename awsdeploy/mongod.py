#!/usr/bin/python
# vim: set expandtab:
from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
from pymongo import *
import config
import sys
import os
import time

@task
def rs_initiate():
    """ Initiate Replica Set On A Single Host  \
    Usage: fab -H <somehost> mongod.rs_initiate"""
    run ('echo "rs.initiate()" | mongo')

@task
def rs_add(member):
    """ Add A Member To The Replica Set, Must Be Run On PRIMARY \
    Usage: fab -H <primary_replica_set_member> mongod.rs_add:<new_member_host_name> """
    run ('echo "rs.add(\'%s\')" | mongo' %(member))

@task
def rs_remove(member):
    """ Remover A Member From A Replica Set, Must Be Run On PRIMARY  \
    Usage: fab -h <primary_replica_set_member> mongod.rs_remove:<hostname_to_be_removed> """
    run ('echo "rs.remove(\'%s\')" | mongo' %(member))

@task
def rs_add_delay(member):
    """ Add A Memeber To A Replica Set With slaveDelay=3600, Must Be Run On PRIMARY \
    Usage: fab -h <primary_replica_set_member> mongod.rs_add_delay:<hostname_of_delayed_secondary_to_add> """
    run ('echo "rs.add(\'%s\'), priority=0, slaveDelay=3600" | mongo' %(member))

@task
def create_five_node_mongo_cluster(setname, node1, node2, node3, node4, node5):
    """ Create a mongo replica set requires 5 hostnames \
    Usage: fab -H <hostname_first_member_of_replica_set> mongod.create_mongo_cluster:<setname,node1,node2,node3,node4> """
    run ('echo "cfg = {_id:\'%s\', members : [{_id:0, host:\'%s\'},{_id:1, host:\'%s\'},{_id:2, host:\'%s\'},{_id:3, host:\'%s\'},{_id:4, host:\'%s\', priority:0, slaveDelay:3600}]}; rs.initiate(cfg)" | /opt/mongodb/mongodb/bin/mongo' %(setname, node1, node2, node3, node4, node5))

@task
def create_three_node_mongo_cluster(setname, node1, node2, node3):
    """ Create a mongo replica set requires 3 hostnames \
    Usage: fab -H <hostname_first_member_of_replica_set> mongod.create_mongo_cluster:<setname,node1,node2,node3> """
    run ('echo "cfg = {_id:\'%s\', members : [{_id:0, host:\'%s\'},{_id:1, host:\'%s\'},{_id:2, host:\'%s\', priority:0, slaveDelay:3600}]}; rs.initiate(cfg)" | /opt/mongodb/mongodb/bin/mongo' %(setname, node1, node2, node3))

@task
def stop():
    """ Stops MongoDB Process  \
    Usage: fab -H <mongodb_host> mongod.stop"""
    sudo ('stop mongodb')

@task
def start():
    """ Starts MongoDB Process  \
    Usage: fab -H <mongodb_host> mongod.start"""
    sudo ('start mongodb')

@task
def restart():
    """ Restarts MongoDB Process  \
    Usage: fab -H <mongodb_host> mongod.restart"""
    stop()
    start()

def mongodb_enc_check(region,name):
    puppet_config = config.puppet_enc(region)
    database = puppet_config['database']
    collection = puppet_config['collection']
    host = puppet_config['host']
    con = Connection(host)
    col = con[database][collection]
    ck_node = col.find_one({ 'node' : name })
    if ck_node:
        print (red("PROBLEM: Node "+name+" Already In MongoDB"))
        sys.exit(1)

def mongodb_app_count(region,az,appname,version,dmz):
    puppet_config = config.puppet_enc(region)
    database = puppet_config['database']
    collection = puppet_config['collection']
    host = puppet_config['host']
    con = Connection(host)
    col = con[database][collection]
    nodes = col.find({ 'node' : { '$regex' : '^'+az+'-'+dmz+'-'+appname+'-'+version+'-.*'}})
    num = 0
    for node in nodes:
        if node:
            node = node['node'].split('.')[0]
            num = node.split('-')[-1] 
    return num

def mongodb_third_count(region,az,appname,dmz):
    puppet_config = config.puppet_enc(region)
    database = puppet_config['database']
    collection = puppet_config['collection']
    host = puppet_config['host']
    con = Connection(host)
    col = con[database][collection]
    nodes = col.find({ 'node' : { '$regex' : '^'+az+'-'+dmz+'-'+appname+'-.*'}})
    num = 0
    for node in nodes:
        print node
        if node:
            node = node['node'].split('.')[0]
            num = node.split('-')[-1] 
    return num

def mongodb_shardnum(region,az,shard,app):
    puppet_config = config.puppet_enc(region)
    database = puppet_config['database']
    collection = puppet_config['collection']
    host = puppet_config['host']
    con = Connection(host)
    col = con[database][collection]
    shard = str(shard) 
    node = col.find_one({ 'node' : { '$regex' : '^'+az+'-pri-'+app+'-mongodb-s'+shard+'.*'}})
    return node

def add_meta_data(region,name,instance_info):
    puppet_config = config.puppet_enc(region)
    database = puppet_config['database']
    collection = puppet_config['meta_collection']
    host = puppet_config['host']
    con = Connection(host)
    col = con[database][collection]
    d = {}
    d['node'] = name
    d['instance_id'] = instance_info.instances[0].id
    d['ip_addr'] = instance_info.instances[0].private_ip_address
    d['architecture'] = instance_info.instances[0].architecture
    d['ami'] = instance_info.instances[0].image_id
    d['size'] = instance_info.instances[0].__dict__['instance_type']
    d['deploy_time'] = instance_info.instances[0].__dict__['launch_time']
    d['root_device_type'] = instance_info.instances[0].__dict__['root_device_type']
    d['subnet_id'] = instance_info.instances[0].__dict__['subnet_id']
    col.insert(d)

def add_public_ip(region,rid,elastic_ip):
    puppet_config = config.puppet_enc(region)
    database = puppet_config['database']
    collection = puppet_config['meta_collection']
    host = puppet_config['host']
    con = Connection(host)
    col = con[database][collection]
    col.update({'instance_id' : rid}, {"$set" : {'elastic_ip': elastic_ip}})
