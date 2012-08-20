#!/usr/bin/python
# vim: set expandtab:
from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
import os
import sys
import time
import puppet
import git
import config
import aws

####
#  Cheetah Deployment
####

@task
def deploy_cheetah(version, az='dev', count='1', size='m1.medium'):
    aws.cleanup()
    aws.app_deploy_generic(version, count=count, size=size, appname='cheetah', puppetClass=('java','cheetah'), az=az)
    aws.cleanup()
