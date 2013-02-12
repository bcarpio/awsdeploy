#!/usr/bin/python
# vim: set expandtab:
from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
import config
import os
import sys
import time

@task
def deploy_static_version_cdn(az,appname,version,package_file):
    r=config.get_conf(az)
    execute(deploy_static_cdn,appname,version,package_file,host=r.static)

@task
def deploy_static_cdn(appname,version,package_file):
  root_dir = '/static/'
  app_dir = os.path.join(root_dir, appname, version)

  """put files on server"""
  if not package_file:
    print "package_file must be provided."
    sys.exit(2)

  if not os.path.isfile(package_file):
    print "Error: package file " + package_file + " does not exist."
    sys.exit(2)
  
  tar_file = os.path.basename(package_file)
    
  tmp_tar_file = os.path.join('/tmp/', tar_file)
  app_tar_file = os.path.join(app_dir, tar_file)

  print put(package_file, tmp_tar_file, use_sudo=True)
  print sudo('chown -R root:root ' + tmp_tar_file)
  print sudo('mkdir -p ' + app_dir)
  print sudo('mv ' + tmp_tar_file + ' ' + app_tar_file)
  print sudo('su - root -c "cd ' + app_dir + '; tar xf ' + tar_file + '"')
  print sudo('su - root -c "cd ' + app_dir +'; rm ' + tar_file + '"')
  print sudo('chown -R root:root ' + app_dir)
