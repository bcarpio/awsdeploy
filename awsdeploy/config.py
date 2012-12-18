#!/usr/bin/python
# vim: set expandtab:
import os

class blob(object): pass
def get_prod_east_conf():
    r=blob()
    r.ami='ami-82fa58eb'
    r.region='us-east-1'
    r.basedn='dc=social,dc=local'
    r.ldap='10.201.2.176'
    r.secret='secret'
    r.sgroup='sg-92c326fd'
    r.domain='social.local'
    r.puppetmaster='10.201.2.10'
    r.admin = "cn=admin,"
    r.zserver = '10.201.6.211'
    r.static = '10.201.2.26'
    return r

def get_devqa_west_conf():
    r=blob()
    r.ami='ami-87712ac2'
    r.zone='us-west-1a'
    r.region='us-west-1'
    r.basedn='dc=manhattan,dc=dev'
    r.ldap='10.52.201.88'
    r.secret='secret'
    r.subnet='subnet-d43b8abd'
    r.sgroup='sg-926578fe'
    r.domain='ecollegeqa.net'
    r.puppetmaster='10.52.201.74'
    r.admin = "cn=admin,"
    r.static = "dev-pri-apache-static-01"
    return r

def get_pqa_west_conf():
    r=blob()
    r.ami='ami-1cdd532c'
    r.region='us-west-2'
    r.basedn='dc=social,dc=local'
    r.ldap='10.252.2.165'
    r.secret='secret'
    r.sgroup='sg-6ef1e302'
    r.domain='social.local'
    r.puppetmaster='10.252.2.27'
    r.admin = "cn=admin,"
    r.zserver = '10.252.6.221'
    r.static = '10.252.2.169'
    return r

def get_conf(az):
    if az in ('use1a', 'use1c', 'use1d'):
        r=get_prod_east_conf()
    if az in ('dev', 'qa'):
        r=get_devqa_west_conf()
    if az in ('usw2a', 'usw2b', 'usw2c'):
        r=get_pqa_west_conf()
    return r

def auth():
    user = 'ubuntu'
    key_filename = os.path.join(os.path.dirname(__file__),'../conf/awsdeploy_key.pem')
    return {'user' : user, 'key_filename' : key_filename}

def get_ec2_conf():
    AWS_ACCESS_KEY_ID = 'AKIAIFY6HFGEYDA5JYKA'
    AWS_SECRET_ACCESS_KEY = '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'
    EC2_KEYPAIR = 'awsdeploy_key'
    return {'AWS_ACCESS_KEY_ID' : AWS_ACCESS_KEY_ID, 'AWS_SECRET_ACCESS_KEY' : AWS_SECRET_ACCESS_KEY, 'EC2_KEYPAIR' : EC2_KEYPAIR}

def region_list():
    region_list = ['us-east-1', 'us-west-2','us-west-1']
    return region_list

def puppet_enc(region):
    database = 'instances'
    collection = 'puppet_enc'
    meta_collection = 'meta_data'
    if region == 'us-west-1':
        host = ['10.52.201.38','10.52.201.29','10.52.201.123','10.52.201.101']
    if region == 'us-west-2':
        host = ['10.252.2.51','10.252.4.29','10.252.6.84']
    if region == 'us-east-1':
        host = ['10.201.2.112','10.201.4.103','10.201.6.17']
    return {'database' : database, 'collection' : collection, 'meta_collection' : meta_collection, 'host' : host}
