#!/usr/bin/python
# vim: set expandtab:
from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response
from fabric.api import *
from fabric.operations import local,put
import os, sys
sys.path.append('../')
from awsdeploy import *
import boto.ec2.elb
import aws_stats
import ebs_volumes
import elastic_ips
import aws_instance

app = Flask(__name__)

#### Home Page

@app.route('/')
def index():
    dict = aws_stats.aws_stats()
    list = dict['list']
    aws_urls = dict['aws_urls']
    return render_template('index.html',list=list,aws_urls=aws_urls)

#### PAGE LINKS

@app.route('/viawest')
def app_route_viawest():
	return render_template('viawest.html')

@app.route('/rackspace')
def app_route_rackspace():
	return render_template('rackspace.html')

@app.route('/pt_pod')
def app_route_ptpod():
	return render_template('pt_pod.html')

@app.route('/cornell')
def app_route_cornell():
	return render_template('cornell.html')

@app.route('/boston')
def app_route_boston():
	return render_template('boston.html')

@app.route('/aws/deploy')
def app_route_aws_deploy():
    return render_template('aws_deploy.html')

#### AWS Web EBS Volume Management 

@app.route('/aws/ebs_volumes/<region>/')
def app_route_ebs_volumes(region=None):
    ebs_vol = ebs_volumes.ebs_volumes(region=region)
    return render_template('ebs_volume.html',ebs_vol=ebs_vol,region=region)

@app.route('/aws/ebs_volumes/<region>/delete/<vol_id>')
def app_route_delete_ebs_vol(region=None,vol_id=None):
    ebs_volumes.delete_ebs_vol(region=region,vol_id=vol_id) 
    return redirect(url_for('app_route_ebs_volumes', region=region))

@app.route('/aws/elastic_ips/<region>/')
def app_route_elastic_ips(region=None):
    un_eli = elastic_ips.unattached_elastic_ips(region=region)
    return render_template('elastic_ip.html',un_eli=un_eli,region=region)

@app.route('/aws/elastic_ips/<region>/delete/<ip>')
def app_route_delete_elastic_ip(region=None,ip=None):
    elastic_ips.delete_unattached_elastic_ip(ip,region)
    return redirect(url_for('app_route_elastic_ips', region=region))


@app.route('/aws/instances/<region>/')
def app_route_instance_list(region=None):
    instance_list = aws_instance.instance_list(region=region)
    return render_template('instances.html', instance_list=instance_list, region=region)

@app.route('/aws/instances/<region>/delete/<hostname>')
def app_route_delete_instances_node(region=None,hostname=None):
    remove_instance(hostname=hostname)
    return redirect(url_for('app_route_instance_list', region=region))

@app.route('/aws/instances/<region>/reboot/<instance_id>')
def app_route_reboot_instance(region=None,instance_id=None):
    aws_instance.reboot_instance(region=region,instance_id=instance_id)
    return redirect(url_for('app_route_instance_list', region=region))

@app.route('/aws/instance_events/<region>/')
def app_route_instance_events(region=None):
    instance_event_list = aws_instance.instance_events(region=region)
    return render_template('instance_events.html', instance_event_list=instance_event_list, region=region)

@app.route('/aws/instance_events/<region>/delete/<hostname>')
def delete_instance_event_node(region=None,hostname=None):
    remove_instance(hostname=hostname)
    return redirect(url_for('app_route_instance_events', region=region))

#### API ROUTES


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

@app.route('/aws/node/deploy/mongodb/<az>/<app>/<shard>')
def deploy_mongodb(az=None,app=None,shard=None):
	dict = deploy_five_node_mongodb_replica_set(az=az,shard=shard,app=app)

@app.route('/aws/node/puppet/apply/<hostname>')
def puppetapply(hostname=None):
	output = execute(puppet.puppetd_test, host=hostname)
	return Response(json.dumps(output), mimetype='application/json')

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')
