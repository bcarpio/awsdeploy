#!/usr/bin/python
# vim: set expandtab:
from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
import os
import sys
import time
import puppet
import git
import config
from aws import *

####
#  Cheetah Deployment
####

@task
def deploy_cheetah(version, az='dev', count='1', size='m1.medium'):
    aws.app_deploy_generic(version, count=count, size=size, appname='cheetah', puppetClass=('java','cheetah'), az=az)

####
#  Redis Deployment
####

@task
def deploy_redis(az='dev'):
    aws.third_party_generic_deployment(appname='redis',puppetClass='redis',az=az,size='m1.small')


####
#  Elastic Search Deployment
####

@task
def deploy_elasticsearch(az='dev'):
    aws.third_party_generic_deployment(appname='elasticsearch',puppetClass='elasticsearch',az=az,size='m1.small')

####
# Load Balancer Deployment
####

@task
def deploy_priv_loadbalancers(appname,az='dev'):
    aws.third_party_generic_deployment(appname='haproxy-'+appname,puppetClass=('haproxy','stunnel'),az=az,size='m1.small')


@task
def deploy_pub_loadbalancers(appname,az):
    allocid = aws.allocate_elastic_ip()
    ip_rid = aws.third_party_generic_deployment(appname='haproxy-'+appname,puppetClass=('haproxy','stunnel'),az=az,size='m1.small',dmz='pub')
    rid = ip_rid['rid']
    time.sleep(30)
    aws.associate_elastic_ip(elasticip=allocid,instance=rid)

####
# Mongodb Deployment
####

@task
def deploy_mongodb_replica_set_pp(shard):
    deploy_four_node_mongodb_replica_set(shard=shard, app='sl')
####
# Remove An Instance
####

@task
def remove_instance(hostname):
    az = hostname.split('-', 1)[0]
    if az in ('use1a', 'use1c', 'use1d'):
        aws.remove_east_ec2_instance(name=hostname)
    if az in ('dev', 'qa'):
        aws.remove_west_ec2_instance(name=hostname)

