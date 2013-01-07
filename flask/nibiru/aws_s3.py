#!/usr/bin/python
# vim: set expandtab:
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
from awsdeploy import *
import boto
from boto.s3.key import Key

def upload_file_s3_bucket(bucket=None,file=None,filename=None,dir=None):
    creds = config.get_ec2_conf()
    conn = boto.connect_s3(aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    bucket = conn.get_bucket(bucket)
    k = Key(bucket)
    k.key = dir + filename
    k.set_contents_from_string(file.readlines())

def get_bucket_list(bucket=None,dir=None):
    bucket_list =  []
    creds = config.get_ec2_conf()
    conn = boto.connect_s3(aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    bucket = conn.get_bucket(bucket)
    for key in bucket.list(dir):
        if key.name != dir:
            file_name = key.name.replace(dir,'')
            bucket_list.append(file_name)
        
    return bucket_list
