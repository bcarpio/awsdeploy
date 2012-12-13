#!/usr/bin/python
# vim: set expandtab:
from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response
from fabric.api import *
from fabric.operations import local,put
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from awsdeploy import *
import boto.ec2.elb

def instance_list(region):
    creds = config.get_ec2_conf()
    conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    instances = conn.get_all_instances()
    instance_list = []
    for instance in instances:
        instance_id = instance.instances[0].__dict__['id']
        instance_info = { 'instance_id' : instance_id }
        if 'Name' in instance.instances[0].__dict__['tags']:
            name = instance.instances[0].__dict__['tags']['Name']
        else:
            name = None
        ip = instance.instances[0].__dict__['private_ip_address']
        status = instance.instances[0].__dict__['_state']
        instance_type = instance.instances[0].__dict__['instance_type']

        instance_info['name'] = name
        instance_info['ip'] = ip
        instance_info['instance_type'] = instance_type
        instance_info['status'] = status


        instance_list.append(instance_info)
    return instance_list

def reboot_instance(region=None,instance_id=None):
    creds = config.get_ec2_conf()  
    conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    instance = conn.get_all_instances(instance_ids=instance_id.encode('ascii'))
    instance[0].instances[0].reboot()

def instance_events(region=None):
    creds = config.get_ec2_conf()
    conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    instances = conn.get_all_instance_status()
    instance_event_list = []
    for instance in instances:
        event = instance.events
        if event:
                i = conn.get_all_instances(instance_ids=instance.id.encode('ascii'))
                name = i[0].instances[0].__dict__['tags']['Name']
                event_info = { 'instance_id' : instance.id, 'name': name, 'event' : instance.events[0].code, 'description' : instance.events[0].description, 'event_before' : instance.events
    [0].not_before, 'event_after': instance.events[0].not_after }
                instance_event_list.append(event_info)
    return instance_event_list


def change_instance_type(region=None,instance_id=None,instanceType=None):
    aws_instance_types = ['m1.small', 'm1.medium', 'm1.large', 'm1.xlarge', 'm3.xlarge', 'm3.2xlarge', 'm2.xlarge', 'm2.2xlarge', 'm2.4xlarge', 'c1.medium', 'c1.xlarge']
    if instanceType in aws_instance_types:
        creds = config.get_ec2_conf()
        conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        instance = conn.get_all_instances(instance_ids=instance_id.encode('ascii'))
        instance[0].instances[0].stop()
        status = instance[0].instances[0].state 
        while status != 'stopped':
            time.sleep(10)
            instance = conn.get_all_instances(instance_ids=instance_id.encode('ascii'))
            status = instance[0].instances[0].state
        
        conn.modify_instance_attribute(instance_id,'instanceType',instanceType)
        instance = conn.get_all_instances(instance_ids=instance_id.encode('ascii'))
        instance[0].instances[0].start()
