#!/usr/bin/python
# vim: set expandtab:
from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
import config
import os
import sys
import time

###
# This Task Does The Following
# * Checks LDAP For Existing Node
# * Creates EC2 Instance
# * Dynamically Generates A user-data script which names the node
# * Tags The Node With The Host Name
# * Updates LDAP With The Nodename And IP
# * Adds The Node To Route 53

def deploy_ec2_ami(name, ami, size, zone, region, basedn, ldap, secret, subnet, sgroup, domain, puppetmaster, admin):
    with settings(
        hide('running', 'stdout')
    ):
        a = local("/usr/bin/ldapsearch -l 120 -x -w %s -D '%s' -b '%s' -h %s  -LLL 'cn=%s'" %(secret,admin+basedn,basedn,ldap,name), capture=True)
        if a:
            print (red("PROBLEM: Node '%s' Already In LDAP")%(name))
            sys.exit(1)
        with lcd(os.path.join(os.path.dirname(__file__),'.')):
            local('cat ../templates/user-data.template | sed -e s/HOSTNAME/%s/g -e s/DOMAIN/%s/g -e s/PUPPETMASTER/%s/g > ../tmp/user-data.sh' %(name,domain,puppetmaster))
            local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-run-instances --instance-initiated-shutdown-behavior stop %s --instance-type %s --availability-zone %s --region %s --key ${EC2_KEYPAIR} --user-data-file ../tmp/user-data.sh --subnet %s --group %s > ../tmp/ec2-run-instances.out' %(ami, size, zone, region, subnet, sgroup))
            if region == 'us-west-1':
                ip = local("cat ../tmp/ec2-run-instances.out | grep INSTANCE | awk '{print $13}'", capture=True)
            if region == 'us-east-1':
                ip = local("cat ../tmp/ec2-run-instances.out | grep INSTANCE | awk '{print $12}'", capture=True)
            rid = local("cat ../tmp/ec2-run-instances.out | grep INSTANCE | awk '{print $2}'", capture=True)
            local('echo %s > ../tmp/instance.out' %(rid))
            local('cat ../templates/template.ldif | sed -e s/HOST/\'%s\'/g -e s/IP/\'%s\'/g -e s/BASEDN/%s/g | ldapadd -x -w %s -D "%s" -h %s' %(name,ip,basedn,secret,admin+basedn,ldap))
            local('. ../conf/awsdeploy.bashrc; /usr/local/bin/route53 add_record Z4512UDZ56AKC '+name+'.asskickery.us A '+ip)
            local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-create-tags %s --region %s --tag Name=%s' %(rid,region,name))
            local('rm ../tmp/user-data.sh')
            local('rm ../tmp/ec2-run-instances.out')
            print (blue("SUCCESS: Node '%s' Deployed To %s")%(name,region))
            local('echo %s >> ../tmp/ip.out' %(ip))
    return ip

###
# These Are The Subnet Specific Tasks For Each AZ In EC2
###

def deploy_west_ec2_ami(name, size='m1.small'):
    r=config.get_devqa_west_conf()
    ip = deploy_ec2_ami(name, r.ami, size, r.zone, r.region, r.basedn, r.ldap, r.secret, r.subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip

def deploy_east_1a_public_1(name, size='m1.small', subnet='subnet-c7fac5af', zone='us-east-1a', sgroup='sg-98c326f7'):
    r=config.get_prod_east_conf()
    ip = deploy_ec2_ami(name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, sgroup, r.domain, r.puppetmaster, r.admin)
    return ip

def deploy_east_1a_private_2(name, size='m1.small', subnet='subnet-dafac5b2', zone='us-east-1a'):
    r=config.get_prod_east_conf()
    ip = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip

def deploy_east_1c_public_3(name, size='m1.small', subnet='subnet-1d373375', zone='us-east-1c', sgroup='sg-98c326f7'):
    r=config.get_prod_east_conf()
    ip = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, sgroup, r.domain, r.puppetmaster, r.admin)
    return ip

def deploy_east_1c_private_4(name, size='m1.small', subnet='subnet-ed373385', zone='us-east-1c'):
    r=config.get_prod_east_conf()
    ip = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip

def deploy_east_1d_private_6(name, size='m1.small', subnet='subnet-8d2632e5', zone='us-east-1d'):
    r=config.get_prod_east_conf()
    ip = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip

####
# EC2 Storage Tasks
####

def create_ebs_volume(size='50',zone='us-east-1a', region='east'):
    if region == 'east':
        r=config.get_prod_east_conf()
    if region == 'west':
        r=config.get_devqa_west_conf
    local('. ../conf/awsdeploy.bashrc; /usr/bin/ec2-create-volume --region %s --size %s --availability-zone %s | awk "{print $2}" > ../tmp/ebs_vol.out' %(r.region, size, zone))

def create_ebs_volume_east_1a(zone='us-east-1a'):
    create_ebs_volume, zone='%s' %(zone)

def create_ebs_volume_east_1c(zone='us-east-1c'):
    create_ebs_volume, zone='%s' %(zone)

def create_ebs_volume_east_1d(zone='us-east-1d'):
    create_ebs_volume, zone='%s' %(zone)

def create_ebs_volume_west(zone='us-west-1a'):
    create_ebs_volume, zone=zone, region='west'

def attach_ebs_volume(device, region='us-east-1'):
    volume = local("cat ../tmp/ebs_vol.out | awk '{print $2}'", capture=True)
    instance = local('cat ../tmp/instance.out', capture=True)
    local('. ../conf/awsdeploy.bashrc; /usr/bin/ec2-attach-volume %s --region %s -i %s -d %s' %(volume,region,instance,device))
    local('rm ../tmp/ebs_vol.out')

####
# Elastic IP Tasks
####

def allocate_elastic_ip(region='us-east-1'):
    allocid = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-allocate-address -d vpc --region %s | awk '{print $4}'" %(region), capture=True)
    return allocid

def associate_elastic_ip(elasticip, instance, region='us-east-1'):
    local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-associate-address -a %s -i %s --region %s' %(elasticip, instance, region))


###
# This Checks The Status Of /home/appuser/finished which is applied by puppet
###

def get_aws_deployment_status():
    with settings(
        hide('running', 'stdout')
    ):
        env.warn_only = True
        status = sudo('ls -al /home/appuser/finished > /dev/null 2>&1; echo $?')
        return status

###
# This Updates LDAP With The Right Puppet Classes
###

def ldap_modify(hostname,puppetClass,az):
    if az in ('use1a', 'use1c', 'use1d'):
        r=config.get_prod_east_conf()
    if az in ('dev', 'qa'):
        r=config.get_devqa_west_conf()
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        local("sed -e s/HOST/%s/g -e s/PUPPETCLASS/%s/g -e s/BASEDN/%s/g ../templates/modify.ldif | /usr/bin/ldapmodify -v -x -w %s -D %s%s -h %s" %(hostname,puppetClass,r.basedn,r.secret,r.admin,r.basedn,r.ldap))


### 
# This the generic application deployment task
###
def app_deploy_generic(appname, version, az, count='1', puppetClass='nodejs', size='m1.small'):
    cleanup()
    if az in ('use1a', 'use1c', 'use1d'):
        r=config.get_prod_east_conf()
    if az in ('dev', 'qa'):
        r=config.get_devqa_west_conf()
    if os.path.exists('../tmp/ip.out'):
        local('rm ../tmp/ip.out')
    count = int(count)
    total = 0
    iplist = []
    hostnamelist = []
    with settings(
        hide('running', 'stdout')
    ):
        while total < count:
            num = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=%s-pri-%s-%s-* | grep cn: | awk '{print $2}' | awk -F- '{print $5}' | tail -1" %(r.secret,r.admin,r.basedn,r.basedn,r.ldap,az,appname,version), capture=True)
            if not num:
                num = 0
            num = int(num) + 1
            num = "%02d" % num
            name = az+'-pri-'+appname+'-'+version+'-'+num
            if az == 'use1a':
                ip = deploy_east_1a_private_2(name=name,size=size)
            if az == 'use1c':
                ip = deploy_east_1c_private_4(name=name,size=size)
            if az == 'dev':
                ip = deploy_west_ec2_ami(name=name,size=size)
            if az == 'qa':
                ip = deploy_west_ec2_ami(name=name,size=size)
            iplist.append(ip)
            hostnamelist.append(name)
            total = int(total) + 1

        for host in hostnamelist:
                if isinstance(puppetClass, basestring):
                    ldap_modify(hostname=host, puppetClass=puppetClass, az=az)
                else:
                    for pclass in puppetClass:
                        ldap_modify(hostname=host, puppetClass=pclass, az=az)

        time.sleep(60)

        if len(iplist) == 1:
            env.parallel = False
        else:
            env.parallel = True

        status = 1
        runs = 0
        authinfo = config.auth()
        env.user = authinfo['user']
        env.key_filename = authinfo['key_filename']
        while status != 0:
            if runs > 60:
                print (red("PROBLEM: Deployment Failed"))
                sys.exit(1)
            get_status = execute(get_aws_deployment_status, hosts=iplist)
            total = 0
            for s in get_status.values():
                s = int(s)
                status = total + s
            time.sleep(10)
            runs += 1
    cleanup()
    return iplist

###
# This cleans up after instance creation
###

def cleanup():
    with settings(
        hide('running', 'stdout', 'warnings', 'stderr')
    ):
        with lcd(os.path.join(os.path.dirname(__file__),'.')):
            env.warn_only = True
            local('rm ../tmp/hostname.out')
            local('rm ../tmp/ip.out')


def main():
    print "This is a python module and should be run as such"

if __name__ == "__main__":
    main()
