from fabric.api import *
from fabric.operations import local,put
import socket
import subprocess
import os

@task
def puppetd_test_noop():
	""" Runs puppetd --test --noop Which Displayed What Will Change """
	sudo('puppetd --test --noop')

@task
# @parallel
def puppetd_test():
	""" Runs puppetd --test Which Will Update Puppet Changes """
	env.warn_only = True
	sudo('puppetd --test')

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
	sudo('puppetca --clean %s' % (host))
