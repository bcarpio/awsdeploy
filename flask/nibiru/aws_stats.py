#!/usr/bin/python
# vim: set expandtab:
from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response
from fabric.api import *
from fabric.operations import local,put
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
from awsdeploy import *
import boto.ec2.elb

def aws_stats():
    aws_urls = ['/aws/api/v1.0/node/deploy/az/appname/version/puppetClass/count/size','/aws/api/v1.0/node/deploy/mongodb/az/app/shard','/aws/api/v1.0/node/undeploy/hostname','/aws/api/v1.0/node/az/pri/appname/ip', '/aws/api/v1.0/node/az/pub/appname/hostname', '/aws/api/v1.0/node/puppet/apply/node_name']

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
            status = vol.status
            if status != 'in-use':
                unattached_ebs = unattached_ebs + 1

        elis = conn.get_all_addresses()
        eli_count = len(elis)


        for eli in elis:
            instance_id = eli.instance_id
            if not instance_id:
                unattached_eli = unattached_eli + 1

        connelb = boto.ec2.elb.connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        elbs = connelb.get_all_load_balancers()
        elb_count = len(elbs)
        out_of_service_elbs = 0
        for elb in elbs:
            inst_health = connelb.describe_instance_health(elb.name)
            for inst_h in inst_health:
                if inst_h.state != 'InService':
                    out_of_service_elbs = out_of_service_elbs +1

        list.append({ 'region' : region, 'zones': zones, 'instance_count' : instance_count, 'ebscount' : ebscount, 'unattached_ebs' : unattached_ebs, 'eli_count' : eli_count, 'unattached_eli' : unattached_eli, 'elb_count' : elb_count, 'event_count' : event_count, 'out_of_service_elbs' : out_of_service_elbs })

    return { 'list' : list, 'aws_urls' : aws_urls }
