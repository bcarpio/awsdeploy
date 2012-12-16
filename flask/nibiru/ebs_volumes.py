#!/usr/bin/python
# vim: set expandtab:
from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response
from fabric.api import *
from fabric.operations import local,put
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
from awsdeploy import *
import boto.ec2.elb

def ebs_volumes(region=None):
        creds = config.get_ec2_conf()
        conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        ebs = conn.get_all_volumes()
        ebs_vol = []
        for vol in ebs:
                state = vol.attachment_state()
                if state == None:
                        ebs_info = { 'id' : vol.id, 'size' : vol.size, 'iops' : vol.iops, 'status' : vol.status }
                        ebs_vol.append(ebs_info)
        return ebs_vol

def delete_ebs_vol(region=None,vol_id=None):
        creds = config.get_ec2_conf()
        conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        vol_id = vol_id.encode('ascii')
        vol_ids = conn.get_all_volumes(volume_ids=vol_id)
        for vol in vol_ids:
                vol.delete()
