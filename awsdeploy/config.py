#!/usr/bin/python
# vim: set expandtab:
admin = "cn=admin,"
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
    return r
