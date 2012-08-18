from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
import subprocess
import os
import sys
import time
import puppet
import git

if os.path.isdir(os.path.join(os.path.dirname(__file__),'../social-manhattan-subway')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../social-manhattan-subway'))
	import subway_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../social-manhattan-ui')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../social-manhattan-ui'))
	import ui_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../spindrift-port-authority')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../spindrift-port-authority'))
	import portauthority_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../learning-exchange-ui')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../learning-exchange-ui'))
	import learning_exchange_ui_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../learning-exchange-api')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../learning-exchange-api'))
	import learning_exchange_api_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../blogs')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../blogs'))
	import blogs_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../follows')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../follows'))
	import follows_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../village')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../village'))
	import village_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../affinity')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../affinity'))
	import affinity_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../ui-delegate')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../ui-delegate'))
	import uidelegate_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../share')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../share'))
	import share_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../social-agent')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../social-agent'))
	import socialagent_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../streams')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../streams'))
	import streams_deploy
if os.path.isdir(os.path.join(os.path.dirname(__file__),'../openclass-toolbar')):
	sys.path.append(os.path.join(os.path.dirname(__file__),'../openclass-toolbar'))
	import gtoolbar_deploy





####
# Global Variables
####

admin = "cn=admin,"

class blob(object): pass
def get_east_conf():
    r=blob()
    r.ami='ami-82fa58eb'
    r.region='us-east-1'
    r.basedn='dc=social,dc=local'
    r.ldap='10.201.2.176'
    r.secret='secret'
    r.sgroup='sg-92c326fd'
    r.domain='social.local'
    r.puppetmaster='10.201.2.10'
    return r

def get_west_conf():
    r=blob()
    r.ami='ami-87712ac2'
    r.zone='us-west-1a'
    r.region='us-west-1'
    r.basedn='dc=manhattan,dc=dev'
    r.ldap='10.52.201.88'
    r.secret='secret'
    r.subnet='subnet-d43b8abd'
    r.sgroup='sg-926578fe'
    r.domain='ecollegeqa.net'
    r.puppetmaster='10.52.74.38'
    return r

@task
def get_aws_deployment_status():
	with settings(
		hide('running', 'stdout')
	):		
		env.warn_only = True
		status = sudo('ls -al /home/appuser/finished > /dev/null 2>&1; echo $?')
		return status

@task
def get_aws_deployment_status_total():
	with settings(
		hide('running', 'stdout', 'stderr')
	):
		ip = local('cat '+os.path.join(os.path.dirname(__file__))+'../tmp/ip.out', capture=True).splitlines()
		ip_total = local('cat ../tmp.ip.out |wc -l')
		if ip_total > 1:
			env.parallel = True	
		else:
			env.parallel = False
		status = execute(get_aws_deployment_status, hosts=ip)
		total = 0
		for s in status.values():
			s = int(s)
			total = total + s
		return total
		

####
# Base EC2 Deployment Task
####

@task
def deploy_ec2_ami(name, puppetClass, ami, size, zone, region, basedn, ldap, secret, subnet, sgroup, domain, puppetmaster):
	with settings(
		hide('running', 'stdout')
	):
		a = local("/usr/bin/ldapsearch -l 120 -x -w %s -D '%s' -b '%s' -h %s  -LLL 'cn=%s'" %(secret,admin+basedn,basedn,ldap,name), capture=True)
		if a:
			print (red("PROBLEM: Node '%s' Already In LDAP")%(name))
			sys.exit(1)
		local('cat ../templates/user-data.template | sed -e s/HOSTNAME/%s/g -e s/DOMAIN/%s/g -e s/PUPPETMASTER/%s/g > ../tmp/user-data.sh' %(name,domain,puppetmaster))
		local('. ../conf/awsdeploy.bashrc; /usr/bin/ec2-run-instances --instance-initiated-shutdown-behavior stop %s --instance-type %s --availability-zone %s --region %s --key ${EC2_KEYPAIR} --user-data-file ../tmp/user-data.sh --subnet %s --group %s > ../tmp/ec2-run-instances.out' %(ami, size, zone, region, subnet, sgroup))
		if region == 'us-west-1':
			ip = local("cat ../tmp/ec2-run-instances.out | tail -1 | awk '{print $13}'", capture=True)
		if region == 'us-east-1':
			ip = local("cat ../tmp/ec2-run-instances.out | tail -1 | awk '{print $12}'", capture=True)
		rid = local("cat ../tmp/ec2-run-instances.out | tail -1 | awk '{print $2}'", capture=True)
		local("cat ../tmp/ec2-run-instances.out | tail -1 | awk '{print $2}' > ../tmp/instance.out")
		local('cat ../templates/template.ldif | sed -e s/HOST/\'%s\'/g -e s/IP/\'%s\'/g -e s/PUPPETCLASS/\'%s\'/g -e s/BASEDN/%s/g | ldapadd -x -w %s -D "%s" -h %s' %(name,ip,puppetClass,basedn,secret,admin+basedn,ldap))
		local('. ../conf/awsdeploy.bashrc; /usr/local/bin/route53 add_record Z4512UDZ56AKC '+name+'.asskickery.us A '+ip)
		local('. ../conf/awsdeploy.bashrc; /usr/bin/ec2-create-tags %s --region %s --tag Name=%s' %(rid,region,name))
		local('rm ../tmp/user-data.sh')
		local('rm ../tmp/ec2-run-instances.out')
		print (blue("SUCCESS: Node '%s' Deployed To %s")%(name,region))
		local('echo %s >> ../tmp/ip.out' %(ip))

@task
def app_deploy_generic(version, count='1', size='m1.small', appname='default', puppetClass='default', az='default'):
	if az in ('use1a', 'use1c', 'use1d'):
		r=get_east_conf()
	if az in ('dev', 'qa'):
		r=get_west_conf()
	if os.path.exists('../tmp/ip.out'):
		local('rm ../tmp/ip.out')
	count = int(count)
	total = 0
	while total < count:
		num = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=%s-pri-%s-%s-* | grep cn: | awk '{print $2}' | awk -F- '{print $5}' | tail -1" %(r.secret,admin,r.basedn,r.basedn,r.ldap,az,appname,version), capture=True)
		if not num:
			num = 0
		num = int(num) + 1
		num = "%02d" % num
		name = az+'-pri-'+appname+'-'+version+'-'+num
		local('echo %s >> ../tmp/hostname.out' %(name))
		if az == 'use1a':
			deploy_east_1a_private_2(name=name,puppetClass=puppetClass,size=size)
		if az == 'use1c':
			deploy_east_1c_private_4(name=name,puppetClass=puppetClass,size=size)
		if az == 'dev':
			deploy_west_ec2_ami(name=name,puppetClass=puppetClass,size=size)
		if az == 'qa':
			deploy_west_ec2_ami(name=name,puppetClass=puppetClass,size=size)
		total = int(total) + 1
		
@task
def ldap_modify(puppetClass,az):
	if az in ('use1a', 'use1c', 'use1d'):
		print az
		r=get_east_conf()
	if az in ('dev', 'qa'):
		r=get_west_conf()
	hostnames = local('cat ../tmp/hostname.out', capture=True)
	for host in hostnames.splitlines():
		local("sed -e s/HOST/%s/g -e s/PUPPETCLASS/%s/g -e s/BASEDN/%s/g ../templates/modify.ldif | /usr/bin/ldapmodify -v -x -w %s -D %s%s -h %s" %(host,puppetClass,r.basedn,r.secret,admin,r.basedn,r.ldap))

@task
def cleanup():
	env.warn_only = True
	local('rm ../tmp/hostname.out')
	local('rm ../tmp/ip.out')

####
# Base EC2 Tasks
####

@task
def deploy_west_ec2_ami(name, puppetClass, size='m1.small'):
	r=get_west_conf()
	deploy_ec2_ami (name, puppetClass, r.ami, size, r.zone, r.region, r.basedn, r.ldap, r.secret, r.subnet, r.sgroup, r.domain, r.puppetmaster)

@task
def deploy_east_1a_public_1(name, puppetClass, size='m1.small', subnet='subnet-c7fac5af', zone='us-east-1a', sgroup='sg-98c326f7'):
	r=get_east_conf()
	deploy_ec2_ami(name, puppetClass, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, sgroup, r.domain, r.puppetmaster)

@task
def deploy_east_1a_private_2(name, puppetClass, size='m1.small', subnet='subnet-dafac5b2', zone='us-east-1a'):
	r=get_east_conf()
	deploy_ec2_ami (name, puppetClass, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster)
	
@task
def deploy_east_1c_public_3(name, puppetClass, size='m1.small', subnet='subnet-1d373375', zone='us-east-1c', sgroup='sg-98c326f7'):
	r=get_east_conf()
	deploy_ec2_ami (name, puppetClass, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, sgroup, r.domain, r.puppetmaster)

@task
def deploy_east_1c_private_4(name, puppetClass, size='m1.small', subnet='subnet-ed373385', zone='us-east-1c'):
	r=get_east_conf()
	deploy_ec2_ami (name, puppetClass, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster)

@task
def deploy_east_1d_private_6(name, puppetClass, size='m1.small', subnet='subnet-8d2632e5', zone='us-east-1d'):
	r=get_east_conf()
	deploy_ec2_ami (name, puppetClass, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster)

####
# EC2 Storage Tasks
####

@task
def create_ebs_volume(size='50',zone='us-east-1a', region='east'):
	if region == 'east':
		r=get_east_conf()
	if region == 'west':
		r=get_west_conf()
	local('. ../conf/awsdeploy.bashrc; /usr/bin/ec2-create-volume --region %s --size %s --availability-zone %s | awk "{print $2}" > ../tmp/ebs_vol.out' %(r.region, size, zone))

@task
def create_ebs_volume_east_1a(zone='us-east-1a'):
	execute(create_ebs_volume, zone='%s' %(zone))

@task
def create_ebs_volume_east_1c(zone='us-east-1c'):
	execute(create_ebs_volume, zone='%s' %(zone))

@task
def create_ebs_volume_east_1d(zone='us-east-1d'):
	execute(create_ebs_volume, zone='%s' %(zone))
 
@task
def create_ebs_volume_west(zone='us-west-1a'):
	execute(create_ebs_volume, zone=zone, region='west')

@task
def attach_ebs_volume(device, region='us-east-1'):
	volume = local("cat ../tmp/ebs_vol.out | awk '{print $2}'", capture=True)
	instance = local('cat ../tmp/instance.out', capture=True)
	local('. ../conf/awsdeploy.bashrc; /usr/bin/ec2-attach-volume %s --region %s -i %s -d %s' %(volume,region,instance,device))
	local('rm ../tmp/ebs_vol.out')

####
# Elastic IP Tasks
####

@task
def allocate_elastic_ip(region='us-east-1'):
	allocid = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-allocate-address -d vpc --region %s | awk '{print $4}'" %(region), capture=True)
	return allocid

@task
def associate_elastic_ip(elasticip, instance, region='us-east-1'):
	local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-associate-address -a %s -i %s --region %s' %(elasticip, instance, region))
 
###############################################################################
# Individual Application Deployument Tasks
###############################################################################

####
# Subway Deployment
####

@task
def deploy_subway(version, az='use1a', count='1', projectRoot='../social-manhattan-subway', size='m1.small'):
	execute(app_deploy_generic, version, count=count, size=size, appname='subway', puppetClass='nodejs', az=az)
	if os.path.isdir('../social-manhattan-subway/fabfile'):
		local('cd ../; mv social-manhattan-subway/fabfile/ social-manhattan-subway/subway_deploy/')
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	execute(subway_deploy.deploy, rootDir='/home/appuser/subway', projectRoot=projectRoot, hosts=ip )
	execute(cleanup)

####
# Social UI Deployment
####

@task
def deploy_socialui(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.small'):
	execute(app_deploy_generic, version, count=count, size=size, appname='socialui', puppetClass='nodejs', az=az)
	if os.path.isdir('../social-manhattan-ui/fabfile'):
		local('cd ../; mv social-manhattan-ui/fabfile/ social-manhattan-ui/ui_deploy/')
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	execute(ui_deploy.deploy, rootDir='/home/appuser/socialui', projectRoot=projectRoot, hosts=ip)
	execute(cleanup)

####
# Port Authority Deployment
####

@task
def deploy_portauthority(version, az='use1a', count='1', projectRoot='../spindrift-port-authority', size='m1.small'):
	execute(app_deploy_generic, version, count=count, size=size, appname='portauthority', puppetClass='nodejs', az=az)
	if os.path.isdir('../spindrift-port-authority/fabfile'):
		local('cd ../; mv spindrift-port-authority/fabfile spindrift-port-authority/portauthority_deploy')
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	execute(portauthority_deploy.deploy, rootDir='/home/appuser/port-authority', projectRoot=projectRoot, hosts=ip )
	execute(cleanup)

####
# Learning Exchange UI
####

@task
def deploy_learning_exchange_ui(packageFile, version, az='use1a', count='1', projectRoot='../learning-exchange-ui', size='m1.small'):
	execute(app_deploy_generic, version, count=count, size=size, appname='exchangeui', puppetClass='nodejs', az=az)
	if os.path.isdir('../learning-exchange-ui/fabfile'):
		local('cd ../; mv learning-exchange-ui/fabfile learning-exchange-ui/learning_exchange_ui_deploy')
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		stats = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	execute(learning_exchange_ui_deploy.deploy_server, packageFile=packageFile, deployDir='/home/appuser/learning-exchange-ui', hosts=ip)
	execute(cleanup)


####
# Learning Exchange API
####

@task
def deploy_learning_exchange_api(packageFile, version, az='use1a', count='1', projectRoot='../learning-exchange-api', size='m1.small'):
	execute(app_deploy_generic, version, count=count, size=size, appname='exchangeapi', puppetClass='nodejs', az=az)
	if os.path.isdir('../learning-exchange-api/fabfile'):
		local('cd ../; mv learning-exchange-api/fabfile learning-exchange-api/learning_exchange_api_deploy')
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	execute(learning_exchange_api_deploy.deploy, packageFile=packageFile, deployDir='/home/appuser/learning-exchange-api', hosts=ip)
	execute(cleanup)

####
#  Persona Deployment
####

@task
def deploy_persona(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='persona', puppetClass='java', az=az)
	execute(ldap_modify,'nodejs',az=az)
	if os.path.isdir('../village/fabfile'):
		local('cd ../; mv village/fabfile village/village_deploy')
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	if az in ('use1a', 'use1c'):
		env.environ = 'prod'
	if az in ('dev'):
		env.environ = 'dev'
	if az in ('qa'):
		env.environ = 'qa'
	env.parallel = False
	env.warn_only = True
	execute(village_deploy.deploy, rootDir='/opt', hosts=ip)
	execute(cleanup)

####
#  Presence Deployment
####

@task
def deploy_presence(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='presence', puppetClass='java', az=az)
	execute(ldap_modify,'nodejs',az=az)
	if os.path.isdir('../affinity/fabfile'):
		local('cd ../; mv affinity/fabfile affinity/affinity_deploy')
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	if az in ('use1a', 'use1c'):
		env.environ = 'prod'
		env.build_properties_file = 'build.ec2-prod.properties'
	if az in ('dev'):
		env.environ = 'dev'
	if az in ('qa'):
		env.environ = 'qa'
		env.build_properties_file = 'build.ec2-qa.properties'
	env.parallel = False
	env.warn_only = True
	env.user = 'ubuntu'
	execute(affinity_deploy.deploy, hosts=ip)
	execute(cleanup)

####
#  Blogs Deployment
####

@task
def deploy_blogs(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='blogs', puppetClass='java', az=az)
	execute(ldap_modify,'nodejs',az=az)
	if os.path.isdir('../blogs/fabfile'):
		local('cd ../; mv blogs/fabfile blogs/blogs_deploy')
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	if az in ('use1a', 'use1c'):
		env.environ = 'prod'
	if az in ('dev'):
		env.environ = 'dev'
	if az in ('qa'):
		env.environ = 'qa'
	env.parallel = False
	execute(blogs_deploy.deploy, rootDir='/opt', hosts=ip)
	execute(cleanup)

####
#  Follows Deployment
####

@task
def deploy_follows(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='follows', puppetClass='java', az=az)
	execute(ldap_modify,'nodejs',az=az)
	if os.path.isdir('../follows/fabfile'):
		local('cd ../; mv follows/fabfile follows/follows_deploy')
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	if az in ('use1a', 'use1c'):
		env.environ = 'prod'
	if az in ('dev'):
		env.environ = 'dev'
	if az in ('qa'):
		env.environ = 'qa'
	env.parallel = False
	execute(follows_deploy.deploy, rootDir='/opt', hosts=ip)
	execute(cleanup)

####
#  Share Deployment
####

@task
def deploy_share(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='share', puppetClass='java', az=az)
	execute(ldap_modify,'nodejs',az=az)
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	if az in ('use1a', 'use1c'):
		env.environ = 'prod'
	if az in ('dev'):
		env.environ = 'dev'
	if az in ('qa'):
		env.environ = 'qa'
	env.parallel = False
	execute(share_deploy.deploy, rootDir='/opt', hosts=ip)
	execute(cleanup)

####
#  Social Agent Deployment
####

@task
def deploy_socialagent(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='socialagent', puppetClass='java', az=az)
	execute(ldap_modify,'nodejs',az=az)
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	if az in ('use1a', 'use1c'):
		env.environ = 'prod'
	if az in ('dev'):
		env.environ = 'dev'
	if az in ('qa'):
		env.environ = 'qa'
	env.parallel = False
	execute(socialagent_deploy.deploy, rootDir='/opt', hosts=ip)
	execute(cleanup)

####
#  Streams Deployment
####

@task
def deploy_streams(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='streams', puppetClass='java', az=az)
	execute(ldap_modify,'nodejs',az=az)
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	if az in ('use1a', 'use1c'):
		env.environ = 'prod'
	if az in ('dev'):
		env.environ = 'dev'
	if az in ('qa'):
		env.environ = 'qa'
	env.parallel = False
	execute(streams_deploy.deploy, rootDir='/opt', hosts=ip)
	execute(cleanup)

####
#  Tags Deployment
####

@task
def deploy_tags(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='tags', puppetClass='java', az=az)
	name = local('cat ../tmp/hostname.out', capture=True)
	execute(ldap_modify,'nodejs',az=az)
	execute(cleanup)

####
#  uidelegate Deployment
####

@task
def deploy_uidelegate(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='uidelegate', puppetClass='java', az=az)
	execute(ldap_modify,'nodejs',az=az)
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	if az in ('use1a', 'use1c'):
		env.environ = 'prod'
	if az in ('dev'):
		env.environ = 'dev'
	if az in ('qa'):
		env.environ = 'qa'
	env.parallel = False
	execute(uidelegate_deploy.deploy, rootDir='/opt', hosts=ip)
	execute(cleanup)

####
#  Cheetah Deployment
####

@task
def deploy_cheetah(version, az='use1a', count='1', environment='prod', projectRoot='../social-manhattan-ui', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='cheetah', puppetClass='java', az=az)
	name = local('cat ../tmp/hostname.out', capture=True)
	execute(ldap_modify,'nodejs',az=az)
	execute(cleanup)

####
#  Exchange Deployment
####

@task
def deploy_exchange(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.small'):
	execute(app_deploy_generic, version, count=count, size=size, appname='exchange', puppetClass='java', az=az)
	name = local('cat ../tmp/hostname.out', capture=True)
	execute(ldap_modify,'nodejs',az=az)
	execute(cleanup)

####
#  gtoolbar Deployment
####

@task
def deploy_gtoolbar(version, az='use1a', count='1', rootDir='/home/appuser', size='m1.medium'):
	execute(app_deploy_generic, version, count=count, size=size, appname='gtoolbar', puppetClass='nodejs', az=az)
	time.sleep(60)
	status = 1
	runs = 0
	while status != 0:
		if runs > 60:
			print (red("PROBLEM: Deployment Failed"))
			sys.exit(1)
		status = execute(get_aws_deployment_status_total)
		status = status['<local-only>']
		time.sleep(10)
		runs += 1
	ip = local('cat ../tmp/ip.out', capture=True).splitlines()	
	if az in ('use1a', 'use1c'):
		env.environ = 'prod'
	if az in ('dev'):
		env.environ = 'dev'
	if az in ('qa'):
		env.environ = 'qa'
	execute(gtoolbar_deploy.deploy, rootDir=rootDir, hosts=ip)
	execute(cleanup)

####
#  gcapi Deployment
####

@task
def deploy_gcapi(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.small'):
	execute(app_deploy_generic, version, count=count, size=size, appname='gcapi', puppetClass='nodejs', az=az)
	name = local('cat ../tmp/hostname.out', capture=True)
	execute(cleanup)

####
#  Redis Deployment
####

@task
def deploy_redis(az,instance,size='m1.small'):
	name= az+'-pri-redis-'+instance
	if az == 'use1a':
		execute(deploy_east_1a_private_2, name=name, puppetClass='redis', size=size)
	if az == 'use1c':
		execute(deploy_east_1c_private_4, name=name, puppetClass='redis', size=size)
	if az == 'dev':
		execute(deploy_west_ec2_ami, name=name, puppetClass='redis', size=size)
	if az == 'qa':
		execute(deploy_west_ec2_ami, name=name, puppetClass='redis', size=size)
	execute(cleanup)

####
#  Elastic Search Deployment
####


@task
def deploy_elasticsearch(version, az='use1a', count='1', projectRoot='../social-manhattan-ui', size='m1.large'):
	execute(app_deploy_generic, version, count=count, size=size, appname='elasticsearch', puppetClass='elasticsearch', az=az)
	execute(cleanup)

@task
def deploy_priv_loadbalancers(az='use1a', count='1', environment='prod', size='m1.small'):
	r=get_east_conf()
	num = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=%s-pri-haproxy-* | grep cn: | awk '{print $2}' | awk -F- '{print $4}' | tail -1" %(r.secret,admin,r.basedn,r.basedn,r.ldap,az), capture=True)	
	if not num:
		num = 0
	num = int(num) + 1
	num = "%02d" % num
	name = az+'-pri-haproxy-'+num
	if az == 'use1a':
		execute(deploy_east_1a_private_2, name=name, puppetClass='haproxy', size=size)
	if az == 'use1c':
		execute(deploy_east_1c_private_4, name=name, puppetClass='haproxy', size=size)
	execute(cleanup)
	

	
@task
def deploy_loadbalancers(az='use1a', count='1', environment='prod', size='m1.small'):
	if az in ('use1a', 'use1c'):
		r=get_east_conf()
	if az in ('dev', 'qa'):
		r=get_west_conf()
	count = int(count)
	total = 0
	while total < count:
		if az not in ('dev','qa'):
			allocid = execute(allocate_elastic_ip)
			allocid = allocid['<local-only>']
		num = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=%s-pub-haproxy-* | grep cn: | awk '{print $2}' | awk -F- '{print $4}' | tail -1" %(r.secret,admin,r.basedn,r.basedn,r.ldap,az), capture=True)
		if not num:
			num = 0
		num = int(num) + 1
		num = "%02d" % num
		name = az+'-pub-haproxy-'+num	
		local('echo %s > ../tmp/hostname.out' %(name))
		if az == 'use1a':
			execute(deploy_east_1a_public_1, name=name, puppetClass='haproxy', size=size)
		if az == 'use1c':
			execute(deploy_east_1c_public_3, name=name, puppetClass='haproxy', size=size)
		if az == 'dev':
			execute(deploy_west_ec2_ami, name=name, puppetClass='haproxy', size=size)
		if az == 'qa':
			execute(deploy_west_ec2_ami, name=name, puppetClass='haproxy', size=size)
		name = local('cat ../tmp/hostname.out', capture=True)
		execute(ldap_modify,'nodejs',az=az)
		execute(ldap_modify,'stunnel',az=az)
		instance = local('cat ../tmp/instance.out', capture=True)
		time.sleep(30)
		if az not in ('dev','qa'):
			execute(associate_elastic_ip, elasticip=allocid, instance=instance)
		local('rm ../tmp/ip.out')
		local('rm ../tmp/instance.out')	
		total = int(total) + 1
	execute(cleanup)

###############################################################################
# Mongodb Deployment Specific Tasks
###############################################################################

@task
def setup_fs_mongodb_aws():
	env.warn_only = True
	sudo('puppetd --test')
	env.warn_only = True
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo('mdadm --create --force --assume-clean -R /dev/md0 -l10 --chunk=256 --raid-devices=4 /dev/xvdf /dev/xvdg /dev/xvdh /dev/xvdi')
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	env.warn_only = False
	sudo('mdadm --create --force --assume-clean -R /dev/md0 -l10 --chunk=256 --raid-devices=4 /dev/xvdf /dev/xvdg /dev/xvdh /dev/xvdi')
	sudo('echo "`mdadm --detail --scan`" | tee -a /etc/mdadm.conf')
	sudo('blockdev --setra 128 /dev/md0')
	sudo('blockdev --setra 128 /dev/xvdf')
	sudo('blockdev --setra 128 /dev/xvdg')
	sudo('blockdev --setra 128 /dev/xvdh')
	sudo('blockdev --setra 128 /dev/xvdi')
	sudo('dd if=/dev/urandom of=/etc/data.key bs=1 count=32')
	time.sleep(5)
	sudo('cat /etc/data.key | cryptsetup luksFormat /dev/md0')
	sudo('cat /etc/data.key | cryptsetup luksOpen /dev/md0 data')
	sudo('pvcreate /dev/mapper/data')
	sudo('vgcreate datavg /dev/mapper/data')
	sudo('lvcreate -l 80%vg -n datalv datavg')
	sudo('lvcreate -l 5%vg -n journallv datavg')
	sudo('mke2fs -t ext4 -F /dev/datavg/datalv')
	sudo('mke2fs -t ext4 -F /dev/datavg/journallv')
	sudo('echo "/dev/datavg/datalv  /data   ext4    defaults,auto,noatime,noexec    0       0" | tee -a /etc/fstab')
	sudo('echo "/dev/datavg/journallv       /journal        ext4    defaults,auto,noatime,noexec    0       0" | tee -a /etc/fstab')
	sudo('mkdir -p /journal')
	sudo('mount -a')
	sudo('mkdir -p /data/db.1/')
	sudo('ln -s /journal /data/db.1/journal')
	sudo('chown -R mongodb:mongodb /data/')
	sudo('chown -R mongodb:mongodb /journal/')

@task
def setup_two_drive_fs_mongodb_aws():
	env.warn_only = True
	sudo('puppetd --test')
	env.warn_only = True
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo('mdadm --create --force --assume-clean -R /dev/md0 -l10 --chunk=256 --raid-devices=4 /dev/xvdf /dev/xvdg /dev/xvdh /dev/xvdi')
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	env.warn_only = False
	sudo('mdadm --create --force --assume-clean -R /dev/md0 -l10 --chunk=256 --raid-devices=2 /dev/xvdf /dev/xvdg')
	sudo('echo "`mdadm --detail --scan`" | tee -a /etc/mdadm.conf')
	sudo('blockdev --setra 128 /dev/md0')
	sudo('blockdev --setra 128 /dev/xvdf')
	sudo('blockdev --setra 128 /dev/xvdg')
	sudo('dd if=/dev/urandom of=/etc/data.key bs=1 count=32')
	time.sleep(5)
	sudo('cat /etc/data.key | cryptsetup luksFormat /dev/md0')
	sudo('cat /etc/data.key | cryptsetup luksOpen /dev/md0 data')
	sudo('pvcreate /dev/mapper/data')
	sudo('vgcreate datavg /dev/mapper/data')
	sudo('lvcreate -l 80%vg -n datalv datavg')
	sudo('lvcreate -l 5%vg -n journallv datavg')
	sudo('mke2fs -t ext4 -F /dev/datavg/datalv')
	sudo('mke2fs -t ext4 -F /dev/datavg/journallv')
	sudo('echo "/dev/datavg/datalv  /data   ext4    defaults,auto,noatime,noexec    0       0" | tee -a /etc/fstab')
	sudo('echo "/dev/datavg/journallv       /journal        ext4    defaults,auto,noatime,noexec    0       0" | tee -a /etc/fstab')
	sudo('mkdir -p /journal')
	sudo('mount -a')
	sudo('mkdir -p /data/db.1/')
	sudo('ln -s /journal /data/db.1/journal')
	sudo('chown -R mongodb:mongodb /data/')
	sudo('chown -R mongodb:mongodb /journal/')

@task
def setup_fs_gluster_aws():
	env.warn_only = True
	sudo('puppetd --test')
	env.warn_only = True
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo('mdadm --create --force --assume-clean -R /dev/md0 -l10 --chunk=256 --raid-devices=4 /dev/xvdf /dev/xvdg /dev/xvdh /dev/xvdi')
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
	env.warn_only = False
	sudo('mdadm --create --force --assume-clean -R /dev/md0 -l10 --chunk=256 --raid-devices=4 /dev/xvdf /dev/xvdg /dev/xvdh /dev/xvdi')
	sudo('echo "`mdadm --detail --scan`" | tee -a /etc/mdadm.conf')
	sudo('blockdev --setra 128 /dev/md0')
	sudo('blockdev --setra 128 /dev/xvdf')
	sudo('blockdev --setra 128 /dev/xvdg')
	sudo('blockdev --setra 128 /dev/xvdh')
	sudo('blockdev --setra 128 /dev/xvdi')
	sudo('dd if=/dev/urandom of=/etc/data.key bs=1 count=32')
	time.sleep(5)
	sudo('cat /etc/data.key | cryptsetup luksFormat /dev/md0')
	sudo('cat /etc/data.key | cryptsetup luksOpen /dev/md0 data')
	sudo('pvcreate /dev/mapper/data')
	sudo('vgcreate datavg /dev/mapper/data')
	sudo('lvcreate -l 100%vg -n datalv datavg')
	sudo('mke2fs -t ext4 -F /dev/datavg/datalv')
	sudo('echo "/dev/datavg/datalv  /data   ext4    defaults,auto,noatime,noexec    0       0" | tee -a /etc/fstab')
	sudo('mkdir -p /data/')
	sudo('mount -a')

@task
def mongo_start():
        """ Starts MongoDB Process  \
        Usage: fab -H <mongodb_host> mongod.start"""
        sudo ('start mongodb')

@task
def mongo_stop():
        """ Stops MongoDB Process  \
        Usage: fab -H <mongodb_host> mongod.stop"""
        sudo ('stop mongodb')

@task
def mongo_backup():
		""" Force A MongoDB Backup"""
		sudo('/opt/mongodb/scripts/snapshot.sh')

@task
def create_mongo_cluster(setname, node1, node2, node3, node4, node5):
        """ Create a mongo replica set requires 5 hostnames \
        Usage: fab -H <hostname_first_member_of_replica_set> mongod.create_mongo_cluster:<setname,node1,node2,node3,node4> """
        run ('echo "cfg = {_id:\'%s\', members : [{_id:0, host:\'%s\'},{_id:1, host:\'%s\'},{_id:2, host:\'%s\'},{_id:3, host:\'%s\'},{_id:4, host:\'%s\', priority:0, slaveDelay:3600}]}; rs.initiate(cfg)" | /opt/mongodb/mongodb/bin/mongo' %(setname, node1, node2, node3, node4, node5))

@task
def create_three_node_mongo_cluster(setname, node1, node2, node3):
        """ Create a mongo replica set requires 3 hostnames \
        Usage: fab -H <hostname_first_member_of_replica_set> mongod.create_mongo_cluster:<setname,node1,node2,node3> """
        run ('echo "cfg = {_id:\'%s\', members : [{_id:0, host:\'%s\'},{_id:1, host:\'%s\'},{_id:2, host:\'%s\', priority:0, slaveDelay:3600}]}; rs.initiate(cfg)" | /opt/mongodb/mongodb/bin/mongo' %(setname, node1, node2, node3))

@task
@task
def deploy_mongodb_replica_set_pp(shard):
	execute(deploy_mongodb_replica_set, shard=shard, app='pp')

@task
def deploy_mongodb_replica_set_sl(shard):
	execute(deploy_mongodb_replica_set, shard=shard, app='sl')

@task
def deploy_mongodb_replica_set(shard='1', setname='mongo', size='m1.xlarge', app='pp'):
	with settings(
		hide('running', 'stdout')
	):
		env.warn_only = True
		local('rm ../tmp/ip.out')
	env.warn_only = False
	r=get_east_conf()
	shardnum = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=use1a-pri-%s-mongodb-s%s* | grep cn: | awk '{print $2}' | awk -F- '{print $5}' | tail -1" %(r.secret,admin,r.basedn,r.basedn,r.ldap,app,shard), capture=True)
	if shardnum:
		print (red("PROBLEM: Shard '%s' Already Exists")%(shard))
		sys.exit(0)	
	# Create First Mongodb Instance With 4 Volumes
	execute(deploy_east_1a_private_2,name='use1a-pri-'+app+'-mongodb-s'+shard+'-01',puppetClass='mongodb',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Second Mongodb Instance With 4 Volumes
	execute(deploy_east_1a_private_2,name='use1a-pri-'+app+'-mongodb-s'+shard+'-02',puppetClass='mongodb',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Third Mongodb Instance With 4 Volumes
	execute(deploy_east_1c_private_4,name='use1c-pri-'+app+'-mongodb-s'+shard+'-01',puppetClass='mongodb',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Forth Mongodb Instance With 4 Volumes
	execute(deploy_east_1c_private_4,name='use1c-pri-'+app+'-mongodb-s'+shard+'-02',puppetClass='mongodb',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Fifth Mongodb Instance With 4 Volumes
	execute(deploy_east_1d_private_6,name='use1d-pri-'+app+'-mongodb-s'+shard+'-01',puppetClass='mongodb',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Setup Mongodb File System	
	time.sleep(300)
	ip_list = local('cat ../tmp/ip.out', capture=True).splitlines()
	execute(setup_fs_mongodb_aws, hosts=ip_list)
	# Start mongodb on each host
	execute(mongo_start, hosts=ip_list)
	# Initiate replica set
	node1 = local('cat ../tmp/ip.out | head -1 | tail -1', capture=True)
	node2 = local('cat ../tmp/ip.out | head -2 | tail -1', capture=True)
	node3 = local('cat ../tmp/ip.out | head -3 | tail -1', capture=True)
	node4 = local('cat ../tmp/ip.out | head -4 | tail -1', capture=True)
	node5 = local('cat ../tmp/ip.out | head -5 | tail -1', capture=True)
	env.user = 'ubuntu'
	execute(create_mongo_cluster, host=node1, setname=setname, node1=node1, node2=node2, node3=node3, node4=node4, node5=node5)
	execute(cleanup)

@task
def deploy_mongodb_three_node_replica_set(shard='1', setname='mongo', size='m1.medium', app='inf'):
	with settings(
		hide('running', 'stdout')
	):
		env.warn_only = True
		local('rm ../tmp/ip.out')
	env.warn_only = False
	r=get_east_conf()
	shardnum = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=use1a-pri-%s-mongodb-s%s* | grep cn: | awk '{print $2}' | awk -F- '{print $5}' | tail -1" %(r.secret,admin,r.basedn,r.basedn,r.ldap,app,shard), capture=True)
	if shardnum:
		print (red("PROBLEM: Shard '%s' Already Exists")%(shard))
		sys.exit(0)	
	# Create First Mongodb Instance With 2 Volumes
	execute(deploy_east_1a_private_2,name='use1a-pri-'+app+'-mongodb-s'+shard+'-01',puppetClass='mongodb',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Second Mongodb Instance With 2 Volumes
	execute(deploy_east_1c_private_4,name='use1c-pri-'+app+'-mongodb-s'+shard+'-01',puppetClass='mongodb',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Third Mongodb Instance With 2 Volumes
	execute(deploy_east_1d_private_6,name='use1d-pri-'+app+'-mongodb-s'+shard+'-01',puppetClass='mongodb',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Setup Mongodb File System	
	time.sleep(300)
	ip_list = local('cat ../tmp/ip.out', capture=True).splitlines()
	execute(setup_two_drive_fs_mongodb_aws, hosts=ip_list)
	# Start mongodb on each host
	execute(mongo_start, hosts=ip_list)
	# Initiate replica set
	node1 = local('cat ../tmp/ip.out | head -1 | tail -1', capture=True)
	node2 = local('cat ../tmp/ip.out | head -2 | tail -1', capture=True)
	node3 = local('cat ../tmp/ip.out | head -3 | tail -1', capture=True)
	env.user = 'ubuntu'
	execute(create_three_node_mongo_cluster, host=node1, setname=setname, node1=node1, node2=node2, node3=node3)
	execute(cleanup)

@task
def deploy_mongodb_dev_instance(app='inf', setname='mongo', size='m1.medium'):
	with settings(
		hide('running', 'stdout')
	):
		env.warn_only = True
		local('rm ../tmp/ip.out')
	env.warn_only = False
	r=get_west_conf()
    # Create First Mongodb Instance With 2 Volumes
	execute(deploy_west_ec2_ami,name='dev-pri-'+app+'-mongodb-01',puppetClass='mongodb',size=size)
	time.sleep(120)
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	time.sleep(300)
	ip_list = local('cat ../tmp/ip.out', capture=True).splitlines()
	execute(setup_two_drive_fs_mongodb_aws, hosts=ip_list)
	execute(mongo_start, hosts=ip_list)
	execute(cleanup)

###
# Gluster
###

@task
def deploy_gluster_prod_avatars():
    execute(deploy_gluster, app='avatars')

@task
def deploy_gluster_prod_elasticsearch():
    execute(deploy_gluster, app='esearch')

@task
def deploy_gluster_dev_avatars():
	execute(deploy_gluster_dev_qa, environment='dev', app='avatars')

@task
def deploy_gluster_dev_elasticsearch():
	execute(deploy_gluster_dev_qa, environment='dev', app='elasticsearch')

@task
def deploy_gluster_qa_avatars():
	execute(deploy_gluster_dev_qa, environment='qa', app='avatars')

@task
def deploy_gluster_qa_elasticsearch():
    execute(deploy_gluster_dev_qa, environment='qa', app='elasticsearch')

@task
def deploy_gluster(app, size='m1.xlarge'):
	with settings(
		hide('running', 'stdout')
	):
		env.warn_only = True
		local('rm ../tmp/ip.out')
	env.warn_only = False
	r=get_east_conf()
	# Create First Gluster Instance With 4 Volumes
	execute(deploy_east_1a_private_2,name='use1a-pri-'+app+'-gluster-01',puppetClass='gluster',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Second Gluster Instance With 4 Volumes
	execute(deploy_east_1a_private_2,name='use1a-pri-'+app+'-gluster-02',puppetClass='gluster',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1a)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Third Gluster Instance With 4 Volumes
	execute(deploy_east_1c_private_4,name='use1c-pri-'+app+'-gluster-01',puppetClass='gluster',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Forth Gluster Instance With 4 Volumes
	execute(deploy_east_1c_private_4,name='use1c-pri-'+app+'-gluster-02',puppetClass='gluster',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1c)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Fifth Gluster Instance With 4 Volumes
	execute(deploy_east_1d_private_6,name='use1d-pri-'+app+'-gluster-01',puppetClass='gluster',size=size)
	time.sleep(120)
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_east_1d)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Setup Gluster File System	
	time.sleep(300)
	ip_list = local('cat ../tmp/ip.out', capture=True).splitlines()
	execute(setup_fs_gluster_aws, hosts=ip_list)
	execute(cleanup)

@task
def deploy_gluster_dev_qa(app, environment='dev', size='m1.xlarge'):
	with settings(
		hide('running', 'stdout')
	):
		env.warn_only = True
		local('rm ../tmp/ip.out')
	env.warn_only = False
	r=get_west_conf()
	# Create First Gluster Instance With 4 Volumes
	execute(deploy_west_ec2_ami,name=environment+'-pri-'+app+'-gluster-01',puppetClass='gluster',size=size)
	time.sleep(120)
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Create Second Gluster Instance With 4 Volumes
	execute(deploy_west_ec2_ami,name=environment+'-pri-'+app+'-gluster-02',puppetClass='gluster',size=size)
	time.sleep(120)
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdf', region='%s' %(r.region))
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdg', region='%s' %(r.region))
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdh', region='%s' %(r.region))
	execute(create_ebs_volume_west)
	time.sleep(5)
	execute(attach_ebs_volume,device='/dev/sdi', region='%s' %(r.region))
	local('rm ../tmp/instance.out')
	# Setup Gluster File System 
	time.sleep(300)
	ip_list = local('cat ../tmp/ip.out', capture=True).splitlines()
	execute(setup_fs_gluster_aws, hosts=ip_list)
	execute(cleanup)

###
# Misc
###

@task
def puppet_clean(name):
	sudo('/usr/sbin/puppetca --clean %s' %(name))

@task
def remove_east_ec2_instance(name, region='us-east-1'):
	r=get_east_conf()
	env.user = 'ubuntu'
	env.warn_only = True
	instance = local(". ../conf/awsdeploy.bashrc; /usr/bin/ec2-describe-instances --region %s --filter tag:Name=%s | grep INSTANCE | awk '{print $2}'" %(region,name), capture=True)
	local('/usr/bin/ldapdelete -x -w %s -D "cn=admin,dc=social,dc=local" -h %s cn=%s,ou=hosts,dc=social,dc=local' %(r.secret,r.ldap,name))
	execute(puppet_clean,name+'.social.local',host='10.201.2.10')
	local('zabbix_api/remove_host.py %s' %(name))
	ip = local("host "+name+".asskickery.us | awk '{print $4}'", capture=True)
	local('. ../conf/awsdeploy.bashrc; /usr/local/bin/route53 del_record Z4512UDZ56AKC '+name+'.asskickery.us. A '+ip)
	local('. ../conf/awsdeploy.bashrc; /usr/bin/ec2-terminate-instances --region %s %s' %(region,instance))

@task
def remove_west_ec2_instance(name, region='us-west-1'):
	r=get_west_conf()
	env.user = 'root'
	env.warn_only = True
	instance = local(". ../conf/awsdeploy.bashrc; /usr/bin/ec2-describe-instances --region %s --filter tag:Name=%s | grep INSTANCE | awk '{print $2}'" %(region,name), capture=True)
	local('/usr/bin/ldapdelete -x -w %s -D "cn=admin,dc=manhattan,dc=dev" -h %s cn=%s,ou=hosts,dc=manhattan,dc=dev' %(r.secret,r.ldap,name))
	execute(puppet_clean,name+'.ecollegeqa.net',host='10.52.74.38')
	ip = local("host "+name+".asskickery.us | awk '{print $4}'", capture=True)
	local('. ../conf/awsdeploy.bashrc; /usr/local/bin/route53 del_record Z4512UDZ56AKC '+name+'.asskickery.us. A '+ip)
	local('. ../conf/awsdeploy.bashrc; /usr/bin/ec2-terminate-instances --region %s %s' %(region,instance))


@task
def compare_ldap_to_ec2(region='us-east-1'):
	with settings(
		hide('running', 'stdout')
	):
		r=get_east_conf()
		env.user = 'ubuntu'
		host_list = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.201.2.176   | grep cn: | awk '{print $2}' | grep -v default | grep -v '\-host'", capture=True).splitlines()
		for host in host_list:
			instance = local(". ../conf/awsdeploy.bashrc; /usr/bin/ec2-describe-instances --region %s --filter tag:Name=%s | tail -1 | awk '{print $5}'" %(region,host), capture=True)	
			if host != instance:
				print (red("Host:" + red(host) + " Not In EC2"))

@task
def compare_ec2_to_ldap():
	with settings(
		hide('running', 'stdout')
	):
		r=get_east_conf()
		env.user = 'ubuntu'
		host_list = local(". ../conf/awsdeploy.bashrc; /usr/bin/ec2-describe-instances --region us-east-1 | grep use | awk '{print $5}'", capture=True).splitlines()
		for host in host_list:
			instance = local("ldapsearch -x -w secret -D 'cn=admin,dc=social,dc=local' -b 'ou=hosts,dc=social,dc=local' -h 10.201.2.176 -LLL 'cn=%s' | grep cn: | awk '{print $2}'" %(host), capture=True)
			if host != instance:
				print (red("Host:" + red(host) + " Not In LDAP"))
