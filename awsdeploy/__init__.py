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
import cassandra
import hadoop
from aws import *
from pymongo import Connection

authinfo = config.auth()
env.user = authinfo['user']
env.key_filename = authinfo['key_filename']

####
#  Cheetah Deployment
####

@task
def deploy_cheetah(version, az='dev', count='1', size='m1.large'):
    aws.app_deploy_generic(version=version, count=count, size=size, appname='cheetah', puppetClass=('java','cheetah', 'nodejs'), az=az)

####
#  Redis Deployment
####

@task
def deploy_redis(az='dev'):
    aws.third_party_generic_deployment(appname='redis',puppetClass='redis',az=az,size='m1.small')

####
# Zookeeper Deployment
####

@task
def deploy_zookeeper(appname,az='dev'):
    aws.third_party_generic_deployment(appname=appname+'-zookeeper',puppetClass=('java','zookeeper'),az=az,size='m1.small')


####
# Apache Deployment
####

@task
def deploy_apache_static(az='dev'):
    aws.third_party_generic_deployment(appname='apache-static',puppetClass='apache_static',az=az,size='m1.small')

####
# Puppetmaster Deployment
####

@task
def deploy_puppetmaster(az='dev'):
    aws.third_party_generic_deployment(appname='puppet',puppetClass='puppetmaster',az=az,size='m1.small')

####
# Java Server Deployment
####

@task
def deploy_java_server(appname,version='0x1x0',az='dev',count='1',size='m1.medium'):
    aws.app_deploy_generic(appname=appname,version=version,puppetClass=('java','nodejs'),az=az,count=count,size=size)


####
# Nginx Server Deployment
####

@task
def deploy_nginx_server(appname,version,az='dev',count='1',size='m1.small'):
    aws.app_deploy_generic(appname=appname,version=version,puppetClass=('nginx','nodejs'),az=az,count=count,size=size)


####
# NodeJs Server Deployment
####

@task
def deploy_node_server(appname,version,az='dev',count='1',size='m1.medium'):
    aws.app_deploy_generic(version=version,appname=appname,puppetClass='nodejs',az=az,count=count,size=size)

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
def deploy_rabbitmq(appname,az='dev'):
    ip = aws.deploy_one_node_with_10_ebs_io_volumes_raid_0(appname=appname+'-rabbitmq',puppetClass=('rabbitmq','stdlib'),az=az,size='m1.xlarge')
    execute(aws.setup_rabbit_lvm,hosts=ip)

####
# Cassandra Deployment
####

@task
def deploy_three_node_cassandra(appname,az='dev'):
    iplist = deploy_three_nodes_with_2_ebs_volumes_raid_0(az=az,appname=appname+'-cassandra',puppetClass=('java','cassandra'),iops='no',capacity='100',size='m1.xlarge')
    execute(aws.setup_gluster_lvm,hosts=iplist)

@task
def deploy_five_node_cassandra(appname,az='dev'):
    iplist = deploy_five_nodes_with_4_ebs_volumes_raid_0(az=az,appname=appname+'-cassandra',puppetClass=('java','cassandra'),iops='no',capacity='100',size='m1.xlarge')
    execute(aws.setup_gluster_lvm,hosts=iplist)
    execute(cassandra.move_cassandra_home_to_data_cassandra,hosts=iplist)

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
    aws.associate_elastic_ip(elasticip=allocid.allocation_id,instance=rid,region=r.region)
    mongod.add_public_ip(region=r.region,rid=rid,elastic_ip=allocid.public_ip)
    iplist = []
    iplist.append(ip_rid['ip'])
    return iplist

####
# Mongodb Deployment
####


@task
def deploy_mongodb_replica_set(az,shard,app):
    deploy_five_node_mongodb_replica_set(az=az,shard=shard,app=app)

###
# Gluster Deployment
###

@task
def deploy_gluster(az,app):
    deploy_five_node_gluster_cluster(az,app=app)

###
# Storm Deployment
###

@task
def deploy_nimbus(appname,az='dev'):
    aws.third_party_generic_deployment(appname=appname+'-nimbus',puppetClass=('java','storm::nimbus','storm::ui'),az=az,size='m1.small')

@task
def deploy_storm(appname,az='dev'):
    aws.third_party_generic_deployment(appname=appname+'-storm',puppetClass=('java','storm::supervisor'),az=az,size='m1.small')

###
# Apt Deployment
###

@task
def deploy_aptrepo(az='dev'):
    aws.third_party_generic_deployment(appname='apt',puppetClass='aptrepo',az=az,size='m1.small')
    
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
    output = [ 'OK' ]
    return output

####
# Compare EC2 to LDAP and Vice Versa
####

@task
def compare_ldap_to_ec2(region='us-east-1'):
    creds = config.get_ec2_conf()
    with settings(
        hide('running', 'stdout')
    ):
        r=config.get_prod_east_conf()
        conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        instances = conn.get_all_instances()
        with lcd(os.path.join(os.path.dirname(__file__),'.')):
            host_list = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.201.2.176   | grep cn: | awk '{print $2}' | grep -v default | grep -v '\-host'", capture=True).splitlines()
            for host in host_list:
                for instance in instances:
                    if 'Name' in instance.instances[0].__dict__['tags']:
                        instance_name = instance.instances[0].__dict__['tags']['Name']
                        if host == instance_name:
                            break
                else:
                    print (red("Host:" + red(host) + " Not In EC2"))
@task
def compare_ec2_to_ldap(region='us-east-1'):
    creds = config.get_ec2_conf()
    with settings(
        hide('running', 'stdout')
    ):
        r=config.get_prod_east_conf()
        conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        instances = conn.get_all_instances() 
        for instance in instances:
            if 'Name' in instance.instances[0].__dict__['tags']:
                name = instance.instances[0].__dict__['tags']['Name']
            else:
                name = None
            host = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.201.2.176 -LLL 'cn=%s' | grep cn: | awk '{print $2}'" %(name), capture=True)
            if host != name:
                print (red("Host:" + red(name) + " Not In LDAP"))
