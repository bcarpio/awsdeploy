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
    aws.third_party_generic_deployment(appname='haproxy-'+appname,puppetClass=('haproxy','stunnel','nodejs'),az=az,size='m1.small')


@task
def deploy_pub_loadbalancers(appname,az):
    allocid = aws.allocate_elastic_ip()
    ip_rid = aws.third_party_generic_deployment(appname='haproxy-'+appname,puppetClass=('haproxy','stunnel','nodejs'),az=az,size='m1.small',dmz='pub')
    rid = ip_rid['rid']
    time.sleep(30)
    aws.associate_elastic_ip(elasticip=allocid,instance=rid)

####
# Mongodb Deployment
####

@task
def deploy_mongodb_replica_set_sl(shard):
    deploy_five_node_mongodb_replica_set(shard=shard, app='sl')

@task
def deploy_mongodb_replica_set_inf(shard):
    deploy_three_node_mongodb_replica_set(shard=shard, app='inf')

###
# Gluster Deployment
###

@task
def deploy_gluster(app):
    deploy_five_node_gluster_cluster(app=app)

    
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


####
# Compare EC2 to LDAP and Vice Versa
####

@task
def compare_ldap_to_ec2(region='us-east-1'):
    with settings(
        hide('running', 'stdout')
    ):
        r=config.get_prod_east_conf()
        with lcd(os.path.join(os.path.dirname(__file__),'.')):
            host_list = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.201.2.176   | grep cn: | awk '{print $2}' | grep -v default | grep -v '\-host'", capture=True).splitlines()
            for host in host_list:
                instance = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-describe-instances --region %s --filter tag:Name=%s | tail -1 | awk '{print $5}'" %(region,host), capture=True)
                if host != instance:
                    print (red("Host:" + red(host) + " Not In EC2"))

@task
def compare_ec2_to_ldap():
    with settings(
        hide('running', 'stdout')
    ):
        r=config.get_prod_east_conf()
        with lcd(os.path.join(os.path.dirname(__file__),'.')):
            host_list = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-describe-instances --region us-east-1 | grep use1 | awk '{print $5}'", capture=True).splitlines()
            for host in host_list:
                instance = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.201.2.176 -LLL 'cn=%s' | grep cn: | awk '{print $2}'" %(host), capture=True)
                if host != instance:
                 print (red("Host:" + red(host) + " Not In LDAP"))

