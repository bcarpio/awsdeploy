#!/usr/bin/python
import sys
from zabbix_api import ZabbixAPI

if (len(sys.argv) < 3):
	print "ERROR: Please Supply A Hostname And Zabbix Server"
	sys.exit(1)

zserver = sys.argv[1]
node = sys.argv[2]

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = 'http://'+zserver+'/zabbix'

# Enter credentials for the Zabbix Web Frontend
username = "admin"
password = "zabbix"

# Connect to the Zabbix web frontend (using the same credentials for HTTPAUTH)
zapi = ZabbixAPI(ZABBIX_SERVER, username, password)

# Login to the Zabbix web frontend / API
zapi.login(username, password)

hosts = zapi.host.get( { 'output' : 'extend', 'filter' : { 'host' : [node] }})
for host in hosts:
	host = host['hostid']

zapi.host.delete({ 'hostid' : host })
