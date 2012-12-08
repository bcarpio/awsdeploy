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
    dict = ebs_volumes.ebs_volumes(region=region)
    ebs_vol = dict['ebs_vol']
    return render_template('ebs_volume.html',ebs_vol=ebs_vol,region=region)

@app.route('/aws/ebs_volumes/<region>/delete/<vol_id>')
def app_route_delete_ebs_vol(region=None,vol_id=None):
    ebs_volumes.delete_ebs_vol(region=region,vol_id=vol_id) 
    return redirect(url_for('app_route_ebs_volumes', region=region))

@app.route('/aws/elastic_ips/<region>/')
def elastic_ips(region=None):
        creds = config.get_ec2_conf()
        conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        elis = conn.get_all_addresses()
        un_eli = []
        for eli in elis:
                instance_id = eli.instance_id
                if not instance_id:
                        eli_info = { 'public_ip' : eli.public_ip, 'domain' : eli.domain}
                        un_eli.append(eli_info)
        return render_template('elastic_ip.html',un_eli=un_eli,region=region)

@app.route('/aws/elastic_ips/<region>/delete/<ip>')
def delete_elastic_ip(region=None,ip=None):
        creds = config.get_ec2_conf()
        conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        ip = ip.encode('ascii')
        elis = conn.get_all_addresses(addresses=ip)

        for eli in elis:
                eli.release()
        return redirect(url_for('elastic_ips', region=region))


@app.route('/aws/instances/<region>/')
def instance_list(region=None):
    creds = config.get_ec2_conf()    
    conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    instances = conn.get_all_instances()
    instance_list = []
    for instance in instances:
        instance_id = instance.instances[0].__dict__['id']
        instance_info = { 'instance_id' : instance_id }
        if 'Name' in instance.instances[0].__dict__['tags']:
            name = instance.instances[0].__dict__['tags']['Name']
        else:
            name = None
        ip = instance.instances[0].__dict__['private_ip_address']
        status = instance.instances[0].__dict__['_state']
        instance_type = instance.instances[0].__dict__['instance_type']

        instance_info['name'] = name
        instance_info['ip'] = ip
        instance_info['instance_type'] = instance_type
        instance_info['status'] = status

        
        instance_list.append(instance_info)
    return render_template('instances.html', instance_list=instance_list, region=region)

@app.route('/aws/instances/<region>/delete/<hostname>')
def delete_instances_node(region=None,hostname=None):
    remove_instance(hostname=hostname)
    return redirect(url_for('instance_list', region=region))

@app.route('/aws/instances/<region>/reboot/<instance_id>')
def reboot_instance(region=None,instance_id=None):
    creds = config.get_ec2_conf()   
    conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    instance = conn.get_all_instances(instance_ids=instance_id.encode('ascii'))
    instance[0].instances[0].reboot()
    return redirect(url_for('instance_list', region=region))

@app.route('/aws/instance_events/<region>/')
def instance_events(region=None):
        creds = config.get_ec2_conf()
        conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
        instances = conn.get_all_instance_status()
        instance_event_list = []
        for instance in instances:
                event = instance.events
                if event:
                        i = conn.get_all_instances(instance_ids=instance.id.encode('ascii'))
                        name = i[0].instances[0].__dict__['tags']['Name']
                        event_info = { 'instance_id' : instance.id, 'name': name, 'event' : instance.events[0].code, 'description' : instance.events[0].description, 'event_before' : instance.events[0].not_before, 'event_after': instance.events[0].not_after }
                        instance_event_list.append(event_info)
        return render_template('instance_events.html', instance_event_list=instance_event_list, region=region)

@app.route('/aws/instance_events/<region>/delete/<hostname>')
def delete_instance_event_node(region=None,hostname=None):
    remove_instance(hostname=hostname)
    return redirect(url_for('instance_events', region=region))

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
