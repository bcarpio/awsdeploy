from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response
from fabric.api import *
from fabric.operations import local,put
import os, sys
sys.path.append('../awsdeploy_python_module/')
from awsdeploy import *
import boto.ec2.elb

app = Flask(__name__)

@app.route('/')
def index():
	aws_urls = ['/aws/node/deploy/az/appname/version/puppetClass/count/size','/aws/node/undeploy/hostname','/aws/node/az/pri/appname/ip', '/aws/node/az/pub/appname/hostname', '/aws/node/puppet/apply/node_name']
	creds = config.get_ec2_conf()

	prodconn = connect_to_region('us-east-1', aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY']) 
	prodzones = prodconn.get_all_zones()	
	prodcount = len(prodconn.get_all_instance_status())  
	prodebs = prodconn.get_all_volumes()
	prodebscount = len(prodebs)
	prod_unattachedebs = 0
	for vol in prodebs:
		state = vol.attachment_state()
		if state == None:
			prod_unattachedebs = prod_unattachedebs + 1

	prodeli = prodconn.get_all_addresses()
	prodeli_count = len(prodeli)
	prod_unattachedeli = 0
	for eli in prodeli:
		instance_id = eli.instance_id
		if instance_id == None:
			prod_unattachedeli = prod_unattachedeli + 1
	
	prodconnelb = boto.ec2.elb.connect_to_region('us-east-1', aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
	prodelb = prodconnelb.get_all_load_balancers()
	prodelb_count = len(prodelb)

	pqaconn = connect_to_region('us-west-2', aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY']) 
	pqazones = pqaconn.get_all_zones()	
	pqacount = len(pqaconn.get_all_instance_status())  
	pqaebs = pqaconn.get_all_volumes()
	pqaebscount = len(pqaebs)
	pqa_unattachedebs = 0
	for vol in pqaebs:
		state = vol.attachment_state()
		if state == None:
			pqa_unattachedebs = pqa_unattachedebs + 1

	pqaeli = pqaconn.get_all_addresses()
	pqaeli_count = len(pqaeli)
	pqa_unattachedeli = 0
	for eli in pqaeli:
		instance_id = eli.instance_id
		if instance_id == None:
			pqa_unattachedeli = pqa_unattachedeli + 1


	pqaconnelb = boto.ec2.elb.connect_to_region('us-west-2', aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
	pqaelb = pqaconnelb.get_all_load_balancers()
	pqaelb_count = len(pqaelb)

	return render_template('index.html',aws_urls=aws_urls, prodzones=prodzones, pqazones=pqazones, prodcount=prodcount, pqacount=pqacount, prodebscount=prodebscount, pqaebscount=pqaebscount, prod_unattachedebs=prod_unattachedebs, pqa_unattachedebs=pqa_unattachedebs, pqaeli_count=pqaeli_count, prodeli_count=prodeli_count, prod_unattachedeli=prod_unattachedeli, pqa_unattachedeli=pqa_unattachedeli, prodelb_count=prodelb_count, pqaelb_count=pqaelb_count)

@app.route('/viawest')
def viawest():
	return render_template('viawest.html')

@app.route('/rackspace')
def rackspace():
	return render_template('rackspace.html')

@app.route('/pt_pod')
def ptpod():
	return render_template('pt_pod.html')

@app.route('/cornell')
def cornell():
	return render_template('cornell.html')

@app.route('/boston')
def boston():
	return render_template('boston.html')


@app.route('/aws/node/<az>/<zone>/<appname>/ip')
def ldapip(zone=None,az=None,appname=None):
	mylist = host_list.ip_ldap_query(zone=zone,az=az,appname=appname)
	return Response(json.dumps(mylist), mimetype='application/json')

@app.route('/aws/node/<az>/<zone>/<appname>/hostname')
def ldaphost(zone=None,az=None,appname=None):
	mylist = host_list.host_ldap_query(zone=zone,az=az,appname=appname)
	return Response(json.dumps(mylist), mimetype='application/json')

@app.route('/aws/node/deploy/<az>/<appname>/<version>/<puppetClass>/<count>/<size>')
def deploy_app_node(az=None,appname=None,version=None,count=None,puppetClass=None,size=None):
	puppetClass = puppetClass.split('&')
	dict = app_deploy_generic(appname=appname, version=version, az=az, count=count, puppetClass=puppetClass, size=size)
	return Response(json.dumps(dict), mimetype='application/json')

@app.route('/aws/node/undeploy/<hostname>')
def undeploy_app_node(hostname=None):
	dict = remove_instance(hostname=hostname)
	return Response(json.dumps(dict), mimetype='application/json')

@app.route('/aws/node/puppet/apply/<hostname>')
def puppetapply(hostname=None):
	output = execute(puppet.puppetd_test, host=hostname)
	return Response(json.dumps(output), mimetype='application/json')

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')
