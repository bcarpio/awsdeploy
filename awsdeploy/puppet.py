from fabric.api import *
from fabric.operations import local,put
import socket
import subprocess
import os

@task
def puppetd_test():
	""" Runs puppetd --test Which Will Update Puppet Changes """
	env.warn_only = True
	env.user = 'ubuntu'
	output = sudo('puppet agent -t')
	return output
	
@task
def puppetca_list():
	""" Runs puppetca --list """
	sudo('puppetca --list')

@task
def puppetca_sign(host):
	""" Runs puppetca --sign <server_name """
	sudo('puppetca --sign %s' % (host))

@task
def puppetca_clean(host):
	""" Runs puppetca --clean <server_name """
	sudo('puppet ca destroy %s' % (host))

@task
def puppet_fix_ssl():
	""" rm -rf /var/lib/puppet/ssl """
	sudo('service puppet stop')
	sudo('rm -rf /var/lib/puppet/ssl/*')
	sudo('puppet agent -t')
	sudo('service puppet start')

def add_puppetClasses_to_mongodb_enc(hostname,puppetClass):
    sudo('/opt/mongodb-enc/scripts/add_node.py -a append -n %s -c %s' %(hostname,puppetClass))

def add_node_to_mongodb_enc(hostname):
    sudo('/opt/mongodb-enc/scripts/add_node.py -a new -i default -n %s' %(hostname))
