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
def move_cassandra_home_to_data_cassandra():
    sudo('mkdir /data/cassandra')
    sudo('chown -R cassandra:cassandra /data/cassandra')
    with cd('/home/cassandra'):
        sudo('tar zcvf - . | (cd /data/cassandra; tar zxvf - .)')
    sudo('rm -rf /home/cassandra/')
    sudo('ln -s /data/cassandra /home/cassandra')
    env.warn_only = True
    sudo("ps -ef | grep cassandra | grep -v grep | awk '{print $2}' | xargs kill -9")
    sudo('/opt/cassandra/apache-cassandra/bin/cassandra')

