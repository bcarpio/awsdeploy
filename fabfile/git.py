from fabric.api import *

@task
def puppet():
	""" Run git pull on /etc/puppet """
	sudo('cd /etc/puppet; git pull')
