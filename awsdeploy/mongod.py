from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
from pymongo import *
import sys
import difflib
import paramiko
import socket
import subprocess
import os
import host_list
import users
import puppet
import argparse
import mongod
import time

@task
def rs_initiate():
	""" Initiate Replica Set On A Single Host  \
	Usage: fab -H <somehost> mongod.rs_initiate"""
	run ('echo "rs.initiate()" | mongo')

@task
def rs_add(member):
	""" Add A Member To The Replica Set, Must Be Run On PRIMARY \
	Usage: fab -H <primary_replica_set_member> mongod.rs_add:<new_member_host_name> """
	run ('echo "rs.add(\'%s\')" | mongo' %(member))

@task
def rs_remove(member):
	""" Remover A Member From A Replica Set, Must Be Run On PRIMARY  \
	Usage: fab -h <primary_replica_set_member> mongod.rs_remove:<hostname_to_be_removed> """
	run ('echo "rs.remove(\'%s\')" | mongo' %(member))

@task
def rs_add_delay(member):
	""" Add A Memeber To A Replica Set With slaveDelay=3600, Must Be Run On PRIMARY \
	Usage: fab -h <primary_replica_set_member> mongod.rs_add_delay:<hostname_of_delayed_secondary_to_add> """
	run ('echo "rs.add(\'%s\'), priority=0, slaveDelay=3600" | mongo' %(member))

@task
def create_mongo_cluster(setname, node1, node2, node3, node4):
	""" Create a mongo replica set requires 4 hostnames \
	Usage: fab -H <hostname_first_member_of_replica_set> mongod.create_mongo_cluster:<setname,node1,node2,node3,node4> """
	run ('echo "cfg = {_id:\'%s\', members : [{_id:0, host:\'%s\'},{_id:1, host:\'%s\'},{_id:2, host:\'%s\'},{_id:3, host:\'%s\', priority:0, slaveDelay:3600}]}; rs.initiate(cfg)" | /opt/mongodb/mongodb/bin/mongo' %(setname, node1, node2, node3, node4))

	
@task
def remove_mongo_data_files():
	""" Removes files from /data/db.1/* """
	sudo('rm -rf /data/db.1/*')

@task
def snapshot_create():
	""" Create LVM Snapshot On Delayed Host (04) \
	Usage: fab -H <delayed_secondary_host_name> mongod.snapshot_create or fab -R <delayed_secondary_role_name> -P mongod.snapshot_create """
	env.warn_only = True
	result = sudo ('ls -al  /dev/datavg/datalv_ss01 > /dev/null')
	if result.failed:
		stop()
		sudo ('umount /data/')
		sudo ('/sbin/lvcreate -l 100%FREE -s -n datalv_ss01 /dev/datavg/datalv')
		sudo ('mkdir /mdb_backup')
		sudo ('mount /dev/datavg/datalv_ss01 /mdb_backup')
		sudo ('mount /data/')
		start()
	else:
		local('echo "Snapshot Exists"')

@task
def snapshot_remove():
	""" Removes LVM Snapshot From Delayed Host (04)  \
	Usage: fab -H <delayed_secondary_host_name> mongod.snapshot_remove or fab -R <delayed_secondary_role_name> -P mongod.snapshot_remove """
	env.warn_only = True
	result = sudo ('/bin/mount | grep mdb_backup > /dev/null')	
	if result.succeeded :
		sudo ('umount /mdb_backup')	
		sudo ('/sbin/lvremove -f /dev/datavg/datalv_ss01')
		sudo ('rmdir /mdb_backup')
	else:
		local('echo "Snapshot Doesn\'t Exist"')

@task
def stop():
	""" Stops MongoDB Process  \
	Usage: fab -H <mongodb_host> mongod.stop"""
	sudo ('stop mongodb')

@task
def start():
	""" Starts MongoDB Process  \
	Usage: fab -H <mongodb_host> mongod.start"""
	sudo ('start mongodb')

@task
def restart():
	""" Restarts MongoDB Process  \
	Usage: fab -H <mongodb_host> mongod.restart"""
	stop()
	start()

@task
def rolling_upgrade(hostname):
	""" Rolling upgrade of mongodb  \
	Usage: fab mongod.rolling_upgrade:<replica_set_member_name>"""
	## Make initial connection to determine which member is the primary node 
	env.user = 'ubuntu'
	conn = Connection('%s'%(hostname))
	db = conn.local
	isMaster = db.command("isMaster")
	ask = (isMaster['ismaster'])
	if ask == True:
		primary = '%s' %(hostname)
		print primary
	else:
		primary = (isMaster['primary'])
		primary = primary.replace(":27017","")
	## Connect to the primary node to check health on the secondary nodes
	conn = Connection('%s'%(primary))
	db = conn.admin
	replSet = db.command("replSetGetStatus")
	## Loop through the secondary hosts
	for secondary in replSet['members']:
		stateStr = str(secondary['stateStr'])
		host = str(secondary['name'])
		host = host.replace(":27017","")
		if stateStr == 'SECONDARY':
			print (blue("Upgrading Host:" + blue(host)))
			print " "
			# Pull in updated binaries using puppet
			execute(puppet.puppetd_test, host='%s' %(host))
			# Restart mongodb
			execute(mongod.restart, host='%s' %(host))
			# Check to make sure the secondary node is recovered before moving on to the next node
			# Sleep 5 just to make sure that the master has been notified that the node is down
			time.sleep(5)
			goodstatus = 'false'
			count = 0
			while goodstatus != 'true':
				# Make sure that the secondary node actually recovers if it doesn't exit the python script and don't continue
				if count < 100:
					replSet = db.command("replSetGetStatus")
					for sec in db.command("replSetGetStatus")['members']:
						h = str(sec['name'])
						h = h.replace(":27017","")
						if h == host:
							s = str(sec['state'])
							if s == '2':
								goodstatus = 'true'
							else:
								goodstatus = 'false'
								count += 1
								time.sleep(2)
				else:
						print (red("PROBLEM: Node '%s' Didn't Upgrade")%(host))
						sys.exit(1)
	for primary in replSet['members']:
		stateStr = str(primary['stateStr'])
		host = str(primary['name'])
		host = host.replace(":27017","")
		state = str(primary['state'])
		if stateStr == 'PRIMARY':
			execute(mongod.stepDown, host='%s' %(host))
			execute(mongod.stop, host='%s' %(host))
			execute(puppet.puppetd_test, host='%s' %(host))
			execute(mongod.start, host='%s' %(host))
	
@task
def stepDown():
	""" Does a stepdown on the PRIMARY node of a replica set \
	Usage: fab -H <mongodb_primary_replica_set_hostname> mongod.stepDown """
	run('echo "rs.stepDown()" | /opt/mongodb/mongodb/bin/mongo')

@task
def remove_mongodb():
	""" Remove Mongodb from /opt/ \  
	Usage: fab -H <mongodb_hostname> mongod.remove_mongodb """
	sudo('rm -rf /opt/mongodb')

@task
def setup_fs_mongodb_aws():
	env.warn_only = True
	sudo('puppetd --test')
	env.warn_only = False
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo('mdadm --create --force --assume-clean -R /dev/md0 -l10 --chunk=256 --raid-devices=4 /dev/xvdf /dev/xvdg /dev/xvdh /dev/xvdi')
	sudo('echo "`mdadm --detail --scan`" | tee -a /etc/mdadm.conf')
	sudo('blockdev --setra 128 /dev/md0')
	sudo('blockdev --setra 128 /dev/xvdf')
	sudo('blockdev --setra 128 /dev/xvdg')
	sudo('blockdev --setra 128 /dev/xvdh')
	sudo('blockdev --setra 128 /dev/xvdi')
	sudo('pvcreate /dev/md0')
	sudo('vgcreate datavg /dev/md0')
	sudo('lvcreate -l 80%vg -n datalv datavg')
	sudo('lvcreate -l 5%vg -n journallv datavg')
	sudo('mke2fs -t ext4 -F /dev/datavg/datalv')
	sudo('mke2fs -t ext4 -F /dev/datavg/journallv')
	sudo('echo "/dev/datavg/datalv	/data	ext4	defaults,auto,noatime,noexec	0	0" | tee -a /etc/fstab')
	sudo('echo "/dev/datavg/journallv	/journal	ext4	defaults,auto,noatime,noexec	0	0" | tee -a /etc/fstab')
	sudo('mkdir -p /journal')
	sudo('mount -a')
	sudo('mkdir -p /data/db.1/')
	sudo('ln -s /journal /data/db.1/journal')
	sudo('chown -R mongodb:mongodb /data/')
	sudo('chown -R mongodb:mongodb /journal/')

@task
def mongo_perf():
	sudo('apt-get install -y tcsh git-core scons g++ libpcre++-dev libboost-dev libreadline-dev libboost-program-options-dev libboost-thread-dev libboost-filesystem-dev libboost-date-time-dev python-pip build-essential python-dev')
	with cd('/var/tmp'):
		sudo('wget http://downloads.mongodb.org/cxx-driver/mongodb-linux-x86_64-v2.0-latest.tgz')
		sudo('tar zxvf mongodb-linux-x86_64-v2.0-latest.tgz')
		with cd('/var/tmp/mongo-cxx-driver-v2.0'):
			sudo('scons')
			sudo('scons install')
		sudo('git clone https://github.com/mongodb/mongo-perf.git')
		with cd('/var/tmp/mongo-perf'):
			sudo('scons benchmark')
			sudo('pip install pymongo==1.8')

@task
def mongo_version_change():
	env.warn_only = True
	sudo('stop mongodb')
	sudo('puppetd --test')
	env.warn_only = False
	sudo('start mongodb')
