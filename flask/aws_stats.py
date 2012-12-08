#!/usr/bin/python
# vim: set expandtab:
from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response
from fabric.api import *
from fabric.operations import local,put
import os, sys
sys.path.append('../')
from awsdeploy import *
import boto.ec2.elb

def aws_stats():
    aws_urls = ['/aws/node/deploy/az/appname/version/puppetClass/count/size','/aws/node/deploy/mongodb/az/app/shard','/aws/node/undeploy/hostname','/aws/node/az/pri/appname/ip', '/aws/node/az/pub/appname/hostname', '/aws/node/puppet/apply/node_name']

    list = []
    creds = config.get_ec2_conf()

    for region in config.region_list():
        conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        zones = conn.get_all_zones()
        instances = conn.get_all_instance_status()
        instance_count = len(instances)
        ebs = conn.get_all_volumes()
        ebscount = len(ebs)
        unattached_ebs = 0
        unattached_eli = 0
        event_count = 0
   
        for instance in instances:
            events = instance.events
            if events:
                event_count = event_count + 1

        for vol in ebs:
            state = vol.attachment_state()
            if state == None:
                unattached_ebs = unattached_ebs + 1

        elis = conn.get_all_addresses()
        eli_count = len(elis)


        for eli in elis:
            instance_id = eli.instance_id
            if not instance_id:
                unattached_eli = unattached_eli + 1

        connelb = boto.ec2.elb.connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        elb = connelb.get_all_load_balancers()
        elb_count = len(elb)
        list.append({ 'region' : region, 'zones': zones, 'instance_count' : instance_count, 'ebscount' : ebscount, 'unattached_ebs' : unattached_ebs, 'eli_count' : eli_count, 'unattached_eli' : unattached_eli, 'elb_count' : elb_count, 'event_count' : event_count})

    return { 'list' : list, 'aws_urls' : aws_urls }
