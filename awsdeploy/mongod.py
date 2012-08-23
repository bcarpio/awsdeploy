#!/usr/bin/python
# vim: set expandtab:
from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
from pymongo import *
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
