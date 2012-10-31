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
    r.puppetmaster='10.52.74.38'
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
