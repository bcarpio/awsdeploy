#!/usr/bin/python
# vim: set expandtab:
from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response, stream_with_context
from fabric.api import *
from fabric.operations import local,put
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
from awsdeploy import *
import boto.ec2.elb
import aws_stats
import ebs_volumes
import elastic_ips
import aws_instance
import elastic_load_balancers
import puppet_enc
import forms
from nibiru import app

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
def aws_app_route_ebs_volumes(region=None):
    ebs_vol = ebs_volumes.ebs_volumes(region=region)
    return render_template('ebs_volume.html',ebs_vol=ebs_vol,region=region)

@app.route('/aws/ebs_volumes/<region>/delete/<vol_id>')
def aws_app_route_delete_ebs_vol(region=None,vol_id=None):
    ebs_volumes.delete_ebs_vol(region=region,vol_id=vol_id) 
    return redirect(url_for('aws_app_route_ebs_volumes', region=region))

#### AWS Web Elastic IP Management 

@app.route('/aws/elastic_ips/<region>/')
def aws_app_route_elastic_ips(region=None):
    un_eli = elastic_ips.unattached_elastic_ips(region=region)
    return render_template('elastic_ip.html',un_eli=un_eli,region=region)

@app.route('/aws/elastic_ips/<region>/delete/<ip>')
def aws_app_route_delete_elastic_ip(region=None,ip=None):
    elastic_ips.delete_unattached_elastic_ip(ip,region)
    return redirect(url_for('aws_app_route_elastic_ips', region=region))


#### AWS Web Instance Management

@app.route('/aws/instances/<region>/')
def aws_app_route_instance_list(region=None):
    aws_instance_types = config.aws_instance_types()
    instance_list = aws_instance.instance_list(region=region)
    return render_template('instances.html', instance_list=instance_list, region=region, aws_instance_types=aws_instance_types)

@app.route('/aws/instances/<region>/delete/<hostname>')
def aws_app_route_delete_instances_node(region=None,hostname=None):
    remove_instance(hostname=hostname)
    return redirect(url_for('aws_app_route_instance_list', region=region))

@app.route('/aws/instances/<region>/reboot/<instance_id>')
def aws_app_route_reboot_instance(region=None,instance_id=None):
    aws_instance.reboot_instance(region=region,instance_id=instance_id)
    return redirect(url_for('aws_app_route_instance_list', region=region))

@app.route('/aws/instance_events/<region>/')
def aws_app_route_instance_events(region=None):
    instance_event_list = aws_instance.instance_events(region=region)
    return render_template('instance_events.html', instance_event_list=instance_event_list, region=region)

@app.route('/aws/instance_events/<region>/delete/<hostname>')
def aws_app_route_delete_instance_event_node(region=None,hostname=None):
    remove_instance(hostname=hostname)
    return redirect(url_for('aws_app_route_instance_events', region=region))

@app.route('/aws/instance_events/<region>/stop_start/<instance_id>')
def aws_app_route_stop_start_instance(region=None,instance_id=None):
    aws_instance.aws_stop_start_instance(region=region,instance_id=instance_id)
    return redirect(url_for('aws_app_route_instance_events', region=region))

@app.route('/aws/instances/<region>/resize/<instance_id>/<instanceType>')
def aws_app_route_reize_instance(region=None,instance_id=None,instanceType=None):
    aws_instance.change_instance_type(region=region,instance_id=instance_id,instanceType=instanceType)
    return redirect(url_for('aws_app_route_instance_list', region=region))
    

#### Aws Elastic LB Management

@app.route('/aws/elastic_load_balancers/<region>')
def aws_app_route_elastic_load_balancers(region=None):
    elbs = elastic_load_balancers.elastic_load_balacner_list(region=region)
    return render_template('elastic_load_balancers.html', elbs=elbs, region=region)

#### Aws Deployment Tasks

@app.route('/aws/deploy/result/<list>')
def aws_app_route_deploy_result(list=None):
    list = list.split(',')
    return render_template('deploy_result.html', list=list)

@app.route('/aws/deploy/java', methods=['GET', 'POST'])
def aws_app_route_deploy_java():
    form = forms.java_deployment(request.form)
    if request.method == 'POST' and form.validate():
        appname = form.appname.data
        version = form.version.data
        count = form.count.data
        size = form.size.data
        az = form.az.data
        list = app_deploy_generic(appname=appname, version=version, az=az, count=count, puppetClass=('java','nodejs'), size=size, dmz='pri')
        list = ",".join(list)
        return redirect(url_for('aws_app_route_deploy_result', list=list))
    return render_template('aws_deploy_java.html', form=form)


#### Puppet ENC

@app.route('/aws/puppet_enc/<region>')
def aws_app_route_puppet_enc(region=None):
    nodes = puppet_enc.puppet_enc(region=region)
    return render_template('puppet_enc.html',nodes=nodes,region=region)

@app.route('/aws/puppet_enc/<region>/edit/<node>')
def aws_app_route_puppet_enc_edit_node(region=None,node=None):
    node_info = puppet_enc.puppet_node_info(region=region,node=node)
    node_meta_data = puppet_enc.meta_data(region=region,node=node)
    return render_template('puppet_enc_edit.html',region=region,node_info=node_info,node_meta_data=node_meta_data)

@app.route('/aws/puppet_enc/<region>/edit/classes/<puppetClasses>/<node>')
def aws_app_route_puppet_enc_change_classes(region=None,puppetClasses=None,node=None):
    classes = puppetClasses.split('&')
    puppet_enc.puppet_node_update_classes(region=region,node=node,classes=classes)
    return redirect(url_for('aws_app_route_puppet_enc_edit_node', region=region, node=node))
 
@app.route('/aws/puppet_enc/apply/<ip>')
def aws_api_route_puppet_apply(ip=None):
    output = execute(puppet.puppetd_test, host=ip)
    output = output.values()
    output = '\n'.join(output)
    return render_template('output.html',output=output)

#### API ROUTES


@app.route('/aws/api/v1.0/node/<az>/<zone>/<appname>/ip')
def aws_api_route_ldapip(zone=None,az=None,appname=None):
	mylist = host_list.ip_ldap_query(zone=zone,az=az,appname=appname)
	return Response(json.dumps(mylist), mimetype='application/json')

@app.route('/aws/api/v1.0/node/<az>/<zone>/<appname>/hostname')
def aws_api_route_ldaphost(zone=None,az=None,appname=None):
	mylist = host_list.host_ldap_query(zone=zone,az=az,appname=appname)
	return Response(json.dumps(mylist), mimetype='application/json')

@app.route('/aws/api/v1.0/node/deploy/<az>/<appname>/<version>/<puppetClass>/<count>/<size>')
def aws_api_route_deploy_app_node(az=None,appname=None,version=None,count=None,puppetClass=None,size=None):
	puppetClass = puppetClass.split('&')
	dict = app_deploy_generic(appname=appname, version=version, az=az, count=count, puppetClass=puppetClass, size=size)
	return Response(json.dumps(dict), mimetype='application/json')

@app.route('/aws/api/v1.0/node/undeploy/<hostname>')
def aws_api_route_undeploy_app_node(hostname=None):
	dict = remove_instance(hostname=hostname)
	return Response(json.dumps(dict), mimetype='application/json')

@app.route('/aws/api/v1.0/node/deploy/mongodb/<az>/<app>/<shard>')
def aws_api_route_deploy_mongodb(az=None,app=None,shard=None):
	dict = deploy_five_node_mongodb_replica_set(az=az,shard=shard,app=app)

@app.route('/aws/api/v1.0/node/puppet/apply/<hostname>')
def aws_api_rouet_puppetapply(hostname=None):
	output = execute(puppet.puppetd_test, host=hostname)
	return Response(json.dumps(output), mimetype='application/json')

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')
