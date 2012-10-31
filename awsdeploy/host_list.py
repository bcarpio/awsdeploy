from fabric.api import *
from fabric.operations import local,put
import socket
import subprocess
import os
import time

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

@task
def prod_blogs():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-blogs* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_follows():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-follows* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_persona():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-persona* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_presence():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-presence* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_share():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-share* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_socialagent():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-socialagent* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_streams():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-streams* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_uidelegate():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-uidelegate* | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

@task
def prod_portauthority():
	ip_list = local("ldapsearch -x -w secret -D cn=admin,dc=social,dc=local -b dc=social,dc=local -h 10.201.2.176 cn=*-pri-portauthority*-01 | grep ipHostNumber | awk '{print $2}'", capture=True).splitlines()
	env.user = 'ubuntu'
	env.hosts = ip_list

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
