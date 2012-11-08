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
import host_list
import mongod
from aws import *

####
#  Cheetah Deployment
####

@task
def deploy_cheetah(version, az='dev', count='1', size='m1.medium'):
    aws.app_deploy_generic(version=version, count=count, size=size, appname='cheetah', puppetClass=('java','cheetah', 'nodejs'), az=az)

####
#  Redis Deployment
####

@task
def deploy_redis(az='dev'):
    aws.third_party_generic_deployment(appname='redis',puppetClass='redis',az=az,size='m1.small')

@task
def deploy_apt_repo(az='dev'):
    aws.third_party_generic_deployment(appname='apt',puppetClass='puppet',az=az,size='m1.small')

####
# Apache Deployment
####

@task
def deploy_apache_static(az='dev'):
    aws.third_party_generic_deployment(appname='apache-static',puppetClass='apache_static',az=az,size='m1.small')

####
# Java Server Deployment
####

@task
def deploy_java_server(appname,az='dev',count='1',size='m1.medium'):
    aws.app_deploy_generic(version='0x1x0',appname=appname,puppetClass=('java','nodejs'),az=az,count=count,size=size)

####
# NodeJs Server Deployment
####

@task
def deploy_node_server(appname,az='dev',count='1',size='m1.medium'):
    aws.app_deploy_generic(version='0x1x0',appname=appname,puppetClass='nodejs',az=az,count=count,size=size)

####
#  Elastic Search Deployment
####

@task
def deploy_elasticsearch(appname,az='dev'):
    aws.third_party_generic_deployment(appname='elasticsearch-'+appname,puppetClass='elasticsearch',az=az,size='m1.small')


####
#  Uptime Deployment
####

@task
def deploy_uptime(az='dev'):
    aws.third_party_generic_deployment(appname='uptime',puppetClass='uptime',az=az,size='m1.small')
    # for now, install mongo and node and uptime app manually

####
#  GrayLog2 Search Deployment
####

@task
def deploy_graylog2(az='dev'):
    aws.third_party_generic_deployment(appname='graylog2',puppetClass=('elasticsearch','graylog2','java','nodejs'),az=az,size='m1.xlarge')

####
# Rabbit MQ Deployment
####

@task
def deploy_rabbitmq(az='dev'):
    ip = aws.deploy_one_node_with_10_ebs_io_volumes_raid_0(appname='rabbitmq',puppetClass=('rabbitmq','stdlib'),az=az,size='m1.xlarge')
    execute(aws.setup_rabbit_lvm,hosts=ip)

####
# Cassandra Deployment
####

@task
def deploy_cassandra(az='dev'):
    iplist = deploy_three_nodes_with_2_ebs_volumes_raid_0(az=az,appname='cassandra',puppetClass='cassandra',iops='no',capacity='100',size='m1.xlarge')
    execute(aws.setup_gluster_lvm,hosts=iplist)

####
# Load Balancer Deployment
####

@task
def deploy_priv_loadbalancers(appname,az='dev'):
    aws.third_party_generic_deployment(appname='haproxy-'+appname,puppetClass=('haproxy','stud','nodejs'),az=az,size='m1.small')


@task
def deploy_pub_loadbalancers(appname,az):
    r=config.get_conf(az)
    allocid = aws.allocate_elastic_ip(region=r.region)
    ip_rid = aws.third_party_generic_deployment(appname='haproxy-'+appname,puppetClass=('haproxy','stud','nodejs'),az=az,size='m1.small',dmz='pub')
    rid = ip_rid['rid']
    time.sleep(30)
    aws.associate_elastic_ip(elasticip=allocid,instance=rid,region=r.region)

####
# Mongodb Deployment
####

@task
def deploy_mongodb_replica_set_sl(az,shard):
    deploy_five_node_mongodb_replica_set(az,shard=shard,app='sl')

@task
def deploy_mongodb_replica_set_gt(az,shard):
    deploy_five_node_mongodb_replica_set(az,shard=shard,app='gt')

@task
def deploy_mongodb_replica_set_inf(az,shard):
    deploy_three_node_mongodb_replica_set(az,shard=shard,app='inf')

@task
def deploy_mongodb_replica_set_gl2(az,shard):
    deploy_three_node_mongodb_replica_set(az,shard=shard,app='gl2')


###
# Gluster Deployment
###

@task
def deploy_gluster(az,app):
    deploy_five_node_gluster_cluster(az,app=app)

    
####
# Remove An Instance
####

@task
def remove_instance(hostname):
    az = hostname.split('-', 1)[0]
    if az in ('use1a', 'use1c', 'use1d', 'usw2a', 'usw2b', 'usw2c'):
        aws.remove_prod_pqa_ec2_instance(name=hostname,az=az)
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

