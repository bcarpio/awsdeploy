#!/usr/bin/python
# vim: set expandtab:
from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response
from fabric.api import *
from fabric.operations import local,put
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
from awsdeploy import *
import boto.ec2.elb
import boto.vpc

def elastic_load_balacner_list(region):
    creds = config.get_ec2_conf()
    conn = boto.ec2.elb.connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    elbs = conn.get_all_load_balancers()
    total_elbs = len(elbs)
    elbs_info = []
    for elb in elbs:
        instance_health_list = []
        elb_instance_health = conn.describe_instance_health(elb.name)
        for instance in elb_instance_health:
            health = instance.state
            instance_id = instance.instance_id
            instance_health_dict = { 'health' : health, 'instance_id' : instance_id }
            instance_health_list.append(instance_health_dict)
        dns_name = elb.dns_name
        health_check = elb.health_check
        listeners = elb.listeners
        subnets = elb.subnets
        regions = boto.ec2.regions(aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        for region_info in regions:
            if region_info.name == region:
                vpc_region = region_info
                break
        vpc_conn = boto.vpc.VPCConnection(aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'],region=vpc_region)
        subnets_info = vpc_conn.get_all_subnets()
        subnet_ips = []
        for subnet in subnets:
            for subnet_info in subnets_info:
                if subnet == subnet_info.id:
                    subnet_ip = subnet_info.cidr_block
                    subnet_ips.append(subnet_ip)
            
        elb_info = { 'name' : elb.name, 'attached_instance_health' : instance_health_list, 'dns_name' : dns_name , 'health_check' : health_check, 'listeners' : listeners, 'subnet_ips' : subnet_ips}
        elbs_info.append(elb_info)
    inst_conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    instance_name = inst_conn.get_all_instances()
    for elb_dict in elbs_info:
        for instance_id_list in elb_dict['attached_instance_health']:        
            for i in instance_name:
                if i.__dict__['instances'][0].id == instance_id_list['instance_id']:
                    if 'Name' in i.instances[0].__dict__['tags']:
                        name = i.instances[0].__dict__['tags']['Name']
                    else:
                        name = None
                    instance_id_list['instance_name'] = name
    return elbs_info

    
