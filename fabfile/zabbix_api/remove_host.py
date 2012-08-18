#!/usr/bin/python
import sys
from zabbix_api import ZabbixAPI

if (len(sys.argv) < 2):
	print "ERROR: Please Supply A Hostname"
	sys.exit(1)

node = sys.argv[1]

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = 'http://10.201.6.211/zabbix'

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

#zapi.user.updateMedia({ 'users' : [{ "userid": "<%= primary_id %>" }], 'medias' : [{ "mediatypeid": "<%= mediatypeid %>", "sendto": (sys.argv[1]), "active": "0", "severity": "63", "period" : "1-7,00:00-23:59;"}]})
#zapi.user.updateMedia({ 'users' : [{ "userid": "<%= secondary_id %>" }], 'medias' : [{ "mediatypeid": "<%= mediatypeid %>", "sendto": (sys.argv[2]), "active": "0", "severity": "63", "period" : "1-7,00:00-23:59;"}]})
