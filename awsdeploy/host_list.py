from fabric.api import *
from fabric.operations import local,put
import socket
import subprocess
import os
import time
import config

@task
def dev():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h http://10.52.201.88 cn=dev-* | grep ipHostNumber | grep -v 10.52.201.74 | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def qa():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h http://10.52.201.88 cn=qa-* | grep ipHostNumber | grep -v 10.52.201.74 | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def pqa():
    social_pqa_ip_list = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.252.2.165  -LLL  cn=usw2* ipHostNumber | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
    env.user = 'ubuntu'
    env.hosts = social_pqa_ip_list

@task
def prod():
    social_prod_ip_list = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.201.2.176  -LLL  cn=use1* ipHostNumber | grep ipHostNumber | awk '{print $2}' | grep -v 10.201.1.5", capture=True).splitlines()
    env.user = 'ubuntu'
    env.hosts = social_prod_ip_list

@task
def prod_blogs():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-blogs* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def pqa_blogs():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.252.4.23 cn=*-pri-blogs* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list
@task
def prod_follows():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-follows* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

def pqa_follows():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.252.4.23 cn=*-pri-follows* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_persona():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-persona* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def pqa_persona():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.252.4.23 cn=*-pri-persona* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_presence():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-presence* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def pqa_presence():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.252.4.23 cn=*-pri-presence* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_share():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-share* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def pqa_share():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.252.4.23 cn=*-pri-share* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_socialagent():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-socialagent* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def pqa_socialagent():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.252.4.23 cn=*-pri-socialagent* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_streams():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-streams* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def pqa_streams():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.252.4.23 cn=*-pri-streams* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_uidelegate():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-uidelegate* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def pqa_uidelegate():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.252.4.23 cn=*-pri-uidelegate* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list


@task
def prod_portauthority():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-portauthority*-01 | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_haproxy():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pub-haproxy* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

def host_ldap_query(zone,az,appname):
    r=config.get_conf(az)
    ip_list = local("/usr/bin/ldapsearch -x -w secret -D cn=admin,"+r.basedn+" -b "+r.basedn+" -h "+r.ldap+" cn="+az+"-"+zone+"-"+appname+"* |grep 'cn:' | awk '{print $2}'", capture=True).splitlines()
    return ip_list

def ip_ldap_query(zone,az,appname):
    r=config.get_conf(az)
    ip_list = local("/usr/bin/ldapsearch -x -w secret -D cn=admin,"+r.basedn+" -b "+r.basedn+" -h "+r.ldap+" cn="+az+"-"+zone+"-"+appname+"* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
    return ip_list

@task
def restart_crowsnest():
	sudo('restart crows-nest')

@task
def start_blogs():
	sudo('start blogs')

@task
def start_follows():
	sudo('start follows')

@task
def start_persona():
	sudo('start village')

@task
def start_presence():
	sudo('service presence start')

@task
def start_share():
	sudo('start share')

@task
def start_socialagent():
	sudo('start socialagent')


@task
def start_streams():
	sudo('start streams')


@task
def start_uidelegate():
	sudo('start ui-delegate')

@task
def stop_blogs():
    sudo('stop blogs')

@task
def stop_follows():
    sudo('stop follows')

@task
def stop_persona():
    sudo('stop village')

@task
def stop_presence():
    sudo('service presence stop')

@task
def stop_share():
    sudo('stop share')

@task
def stop_socialagent():
    sudo('stop socialagent')


@task
def stop_streams():
    sudo('stop streams')


@task
def stop_uidelegate():
    sudo('stop ui-delegate')


@task
def restart_harbor():
	sudo('stop spindrift-harbor')
	sudo('start spindrift-harbor')

@task
def change_dev_puppet():
	sudo('sed s/^10.52.74.38.*/"10.52.201.74    dev-pri-puppet-01.ecollegeqa.net  dev-pri-puppet-01 puppet"/g -i /etc/hosts')
	sudo('rm -rf /var/lib/puppet/ssl/*')
	env.warn_only = True
	sudo('puppet agent -t')
