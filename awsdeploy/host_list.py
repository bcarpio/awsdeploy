from fabric.api import *
from fabric.operations import local,put
import socket
import subprocess
import os

@task
def pqa():
    social_pqa_ip_list = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.252.2.165  -LLL  cn=usw2* ipHostNumber | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
    env.user = 'ubuntu'
    env.hosts = social_pqa_ip_list

@task
def pqa_nopuppet_master():
    social_pqa_ip_list = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.252.2.165  -LLL  cn=usw2* ipHostNumber | grep ipHostNumber | grep -v 10.252.2.27 | awk '{print $2}'", capture=True).splitlines()
    env.user = 'ubuntu'
    env.hosts = social_pqa_ip_list
@task
def prod():
    social_prod_ip_list = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.201.2.176  -LLL  cn=use1* ipHostNumber | grep ipHostNumber | awk '{print $2}' | grep -v 10.201.1.5", capture=True).splitlines()
    env.user = 'ubuntu'
    env.hosts = social_prod_ip_list
