#!/usr/bin/python
# vim: set expandtab:
from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response
from fabric.api import *
from fabric.operations import local,put
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__),'../'))
from awsdeploy import *
import boto.ec2.elb

def unattached_elastic_ips(region):
    creds = config.get_ec2_conf()
    conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    elis = conn.get_all_addresses()
    un_eli = []
    for eli in elis:
            instance_id = eli.instance_id
            if not instance_id:
                    eli_info = { 'public_ip' : eli.public_ip, 'domain' : eli.domain}
                    un_eli.append(eli_info)
    return un_eli

def delete_unattached_elastic_ip(ip,region):
    creds = config.get_ec2_conf()
    conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    ip = ip.encode('ascii')
    elis = conn.get_all_addresses(addresses=ip)
    for eli in elis:
        eli.release()
