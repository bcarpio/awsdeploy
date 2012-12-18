#!/usr/bin/python
# vim: set expandtab:
# vim: set tabstop=4
# vim: set shiftwidth=4
from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
import os
import sys
import time

@task
def deploy_nibiru():
    with cd('/home/appuser/nibiru'):
        run('git pull origin nibiru')
        sudo('service apache2 restart')
