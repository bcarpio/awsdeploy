#!/usr/bin/python
# vim: set expandtab:
from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *
import config
import os
import sys
import time
import puppet
import mongod
import ldap
import ldap.modlist as modlist
import boto
from boto.ec2 import *
from boto.route53.record import ResourceRecordSets

####
# Define Some Global Values
####
env.skip_bad_hosts = True
env.connection_attempts = 10

####
# This Task Does The Following
# * Checks LDAP For Existing Node
# * Creates EC2 Instance
# * Dynamically Generates A user-data script which names the node
# * Tags The Node With The Host Name
# * Updates LDAP With The Nodename And IP
# * Adds The Node To Route 53
####

def deploy_ec2_ami(name, ami, size, zone, region, basedn, ldaphost, secret, subnet, sgroup, domain, puppetmaster, admin):
    creds = config.get_ec2_conf()
    if "." in name:
        print (red("PROBLEM: Do Not Use Periods In Names"))
    ldap_check(ldaphost,basedn,name)
    template = open(os.path.join(os.path.dirname(__file__),'../templates/user-data.template')).read()
    user_data = template.replace('HOSTNAME',name).replace('DOMAIN',domain).replace('PUPPETMASTER',puppetmaster)
    ec2conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    instance_info = ec2conn.run_instances(
        image_id=ami,
        key_name=creds['EC2_KEYPAIR'],
        instance_type=size,
        security_group_ids=[sgroup],
        instance_initiated_shutdown_behavior='stop',
        placement=zone,
        disable_api_termination=False,
        subnet_id=subnet,
        user_data=user_data
    )
    rid = instance_info.instances[0].id
    ip = instance_info.instances[0].private_ip_address
    time.sleep(2)
    ldap_add(ldaphost,admin,basedn,secret,name,ip)
    update_dns(name,ip)
    ec2conn.create_tags([rid], {'Name': name})
    #execute(add_node_to_mongodb_enc,name,host=puppetmaster)
    print (blue("SUCCESS: Node '%s' Deployed To %s")%(name,region))
    return {'ip': ip, 'rid' : rid}

###
# These Are The Subnet Specific Tasks For Each AZ In EC2
###

def deploy_west_ec2_ami(name, size='m1.small'):
    r=config.get_devqa_west_conf()
    ip_rid = deploy_ec2_ami(name, r.ami, size, r.zone, r.region, r.basedn, r.ldap, r.secret, r.subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_east_1a_public_1(name, size='m1.small', subnet='subnet-c7fac5af', zone='us-east-1a', sgroup='sg-98c326f7'):
    r=config.get_prod_east_conf()
    ip_rid = deploy_ec2_ami(name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_east_1a_private_2(name, size='m1.small', subnet='subnet-dafac5b2', zone='us-east-1a'):
    r=config.get_prod_east_conf()
    ip_rid = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_east_1c_public_3(name, size='m1.small', subnet='subnet-1d373375', zone='us-east-1c', sgroup='sg-98c326f7'):
    r=config.get_prod_east_conf()
    ip_rid = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_east_1c_private_4(name, size='m1.small', subnet='subnet-ed373385', zone='us-east-1c'):
    r=config.get_prod_east_conf()
    ip_rid = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_east_1d_private_6(name, size='m1.small', subnet='subnet-8d2632e5', zone='us-east-1d'):
    r=config.get_prod_east_conf()
    ip_rid = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_west_2a_public_1(name, size='m1.small', subnet='subnet-105def79', zone='us-west-2a', sgroup='sg-92f0e2fe'):
    r=config.get_pqa_west_conf()
    ip_rid = deploy_ec2_ami(name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_west_2a_private_2(name, size='m1.small', subnet='subnet-165def7f', zone='us-west-2a'):
    r=config.get_pqa_west_conf()
    ip_rid = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_west_2b_public_3(name, size='m1.small', subnet='subnet-ef5def86', zone='us-west-2b', sgroup='sg-92f0e2fe'):
    r=config.get_pqa_west_conf()
    ip_rid = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_west_2b_private_4(name, size='m1.small', subnet='subnet-e05def89', zone='us-west-2b'):
    r=config.get_pqa_west_conf()
    ip_rid = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid

def deploy_west_2c_private_6(name, size='m1.small', subnet='subnet-f85def91', zone='us-west-2c'):
    r=config.get_pqa_west_conf()
    ip_rid = deploy_ec2_ami (name, r.ami, size, zone, r.region, r.basedn, r.ldap, r.secret, subnet, r.sgroup, r.domain, r.puppetmaster, r.admin)
    return ip_rid



####
# EC2 Storage Tasks
####

def create_ebs_volume(az,size='50',iops='no'):
    r=config.get_conf(az)
    creds = config.get_ec2_conf()
    ec2conn = connect_to_region(r.region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
    if az == 'use1a':
        zone = 'us-east-1a'
    elif az == 'use1c':
        zone = 'us-east-1c'
    elif az == 'use1d':
        zone = 'us-east-1d'
    elif az == 'usw2a':
        zone = 'us-west-2a'
    elif az == 'usw2b':
        zone = 'us-west-2b'
    elif az == 'usw2c':
        zone = 'us-west-2c'
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        if iops == 'no':
            ebs_vol = ec2conn.create_volume(size, zone)
        elif iops == 'yes':
            ebs_vol = ec2conn.create_volume(size, zone, volume_type='io1', iops='1000')
    return ebs_vol

def attach_ebs_volume(device, ebs_vol, rid, region):
    ebs_vol.attach(rid, device)

####
# Elastic IP Tasks
####

def allocate_elastic_ip(region='us-east-1'):
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        allocid = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-allocate-address -d vpc --region %s | awk '{print $4}'" %(region), capture=True)
    return allocid

def associate_elastic_ip(elasticip, instance, region='us-east-1'):
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-associate-address -a %s -i %s --region %s' %(elasticip, instance, region))


#### 
# Route 53 DNS
####

def update_dns(name,ip):
    creds = config.get_ec2_conf()
    route53conn = boto.connect_route53(creds['AWS_ACCESS_KEY_ID'],creds['AWS_SECRET_ACCESS_KEY'])
    changes = ResourceRecordSets(route53conn, hosted_zone_id='Z4512UDZ56AKC')
    change = changes.add_change("CREATE", name+".asskickery.us", type="A", ttl="600")
    change.add_value(ip)
    changes.commit()

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

def ldap_check(ldaphost,basedn,name):
    ldapinit = ldap.initialize('ldap://'+ldaphost)
    ck_node = ldapinit.search_s(basedn,ldap.SCOPE_SUBTREE, '(cn='+name+')',['cn'])
    if ck_node:
        print (red("PROBLEM: Node "+name+" Already In LDAP"))
        sys.exit(1)

def ldap_add(ldaphost,admin,basedn,secret,name,ip):
    name = name.encode('ascii')
    ldapinit = ldap.initialize('ldap://'+ldaphost)
    ldapinit.simple_bind_s(admin+basedn,secret)
    dn='cn='+name+',ou=hosts,'+basedn
    attrs = {}
    attrs['cn'] = name
    attrs['objectclass'] = ['top','device','ipHost', 'puppetClient']
    attrs['environment'] = 'production'
    attrs['ipHostNumber'] = str(ip)
    attrs['parentnode'] = 'default'
    ldif = modlist.addModlist(attrs)
    ldapinit.add_s(dn,ldif)
    ldapinit.unbind_s()

def ldap_modify(hostname,puppetClass,az):
    r=config.get_conf(az)
    ldapinit = ldap.initialize('ldap://'+r.ldap)
    ldapinit.simple_bind_s(r.admin+r.basedn,r.secret)
    dn='cn='+hostname+',ou=hosts,'+r.basedn
    puppetClass = puppetClass.encode('ascii')
    mod_attrs = [( ldap.MOD_ADD, 'puppetClass', puppetClass)]
    ldapinit.modify_s(dn, mod_attrs)

###
# This Updates Mongodb With The Right Puppet Classes
###
def add_puppetClasses_to_mongodb_enc(hostname,puppetClass):
    sudo('/opt/mongodb-enc/scripts/add_node.py -a append -n %s -c %s' %(hostname,puppetClass))

###
# This adds the node to mongodb enc
###
def add_node_to_mongodb_enc(hostname):
    sudo('/opt/mongodb-enc/scripts/add_node.py -a new -i default -n %s' %(hostname))

### 
# This the generic application deployment task
###
def app_deploy_generic(appname, version, az, count='1', puppetClass='nodejs', size='m1.small'):
    r=config.get_conf(az)
    authinfo = config.auth()
    env.user = authinfo['user']
    env.key_filename = authinfo['key_filename']
    version = version.replace('.','x')
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
                ip_rid = deploy_east_1a_private_2(name=name,size=size)
                ip = ip_rid['ip']
            if az == 'use1c':
                ip_rid = deploy_east_1c_private_4(name=name,size=size)
                ip = ip_rid['ip']
            if az == 'usw2a':
                ip_rid = deploy_west_2a_private_2(name=name,size=size)
                ip = ip_rid['ip']
            if az == 'usw2b':
                ip_rid = deploy_west_2b_private_4(name=name,size=size)
                ip = ip_rid['ip']
            if az == 'dev':
                ip_rid = deploy_west_ec2_ami(name=name,size=size)
                ip = ip_rid['ip']
            if az == 'qa':
                ip_rid = deploy_west_ec2_ami(name=name,size=size)
                ip = ip_rid['ip']
            iplist.append(ip)
            hostnamelist.append(name)
            total = int(total) + 1

        for host in hostnamelist:
                if isinstance(puppetClass, basestring):
                    ldap_modify(hostname=host, puppetClass=puppetClass, az=az)
                #    execute(add_puppetClasses_to_mongodb_enc,hostname=host,puppetClass=puppetClass,hosts=r.puppetmaster)
                else:
                    for pclass in puppetClass:
                        ldap_modify(hostname=host, puppetClass=pclass, az=az)
                #        execute(add_puppetClasses_to_mongodb_enc,hostname=host,puppetClass=puppetClass,hosts=r.puppetmaster)

        time.sleep(120)

        if len(iplist) == 1:
            env.parallel = False
        else:
            env.parallel = True

        status = 1
        runs = 0
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

####
#  3rd Party Deployment
####

def third_party_generic_deployment(appname,puppetClass,az,size='m1.small',dmz='pri'):
    cleanup()
    r=config.get_conf(az)
    authinfo = config.auth()
    env.user = authinfo['user']
    env.key_filename = authinfo['key_filename']
    last = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=%s-%s-%s-* | grep cn: | tail -1" %(r.secret,r.admin,r.basedn,r.basedn,r.ldap,az,dmz,appname), capture=True)
    if last:
        num = last[-2:]
    else:
        num = 0
    num = int(num) + 1
    num = "%02d" % num
    name= az+'-'+dmz+'-'+appname+'-'+num

    if dmz == 'pri':
        if az == 'use1a':
            ip_rid = deploy_east_1a_private_2(name=name,size=size)
        if az == 'use1c':
            ip_rid = deploy_east_1c_private_4(name=name,size=size)
        if az == 'use1d':
            ip_rid = deploy_east_1d_private_6(name=name,size=size)
        if az == 'usw2a':
            ip_rid = deploy_west_2a_private_2(name=name,size=size)
        if az == 'usw2b':
            ip_rid = deploy_west_2b_private_4(name=name,size=size)
        if az == 'usw2c':
            ip_rid = deploy_west_2c_private_6(name=name,size=size)
        if az == 'dev':
            ip_rid = deploy_west_ec2_ami(name=name,size=size)
        if az == 'qa':
            ip_rid = deploy_west_ec2_ami(name=name,size=size)
    elif dmz == 'pub':
        if az == 'use1a':
            ip_rid = deploy_east_1a_public_1(name=name,size=size)
        if az == 'use1c':
            ip_rid = deploy_east_1c_public_3(name=name,size=size)
        if az == 'usw2a':
            ip_rid = deploy_west_2a_public_1(name=name,size=size)
        if az == 'usw2b':
            ip_rid = deploy_west_2b_public_3(name=name,size=size)
    else:
        print "ERROR: Wrong dmz specified"

    if isinstance(puppetClass, basestring):
        ldap_modify(hostname=name, puppetClass=puppetClass, az=az)
    #    execute(add_puppetClasses_to_mongodb_enc,hostname=name,puppetClass=puppetClass,host=r.puppetmaster)
    else:
        for pclass in puppetClass:
            ldap_modify(hostname=name, puppetClass=pclass, az=az)
    #        execute(add_puppetClasses_to_mongodb_enc,hostname=name,puppetClass=puppetClass,host=r.puppetmaster)
    cleanup() 
    return ip_rid

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


####
# Remove EC2 Instance, Clean Puppet, Clean LDAP, Clea Route53, Clean Zabbix
####

def remove_prod_pqa_ec2_instance(name, az):
    r=config.get_conf(az)
    authinfo = config.auth()
    env.user = authinfo['user']
    env.key_filename = authinfo['key_filename']
    env.warn_only = True
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        instance = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-describe-instances --region %s --filter tag:Name=%s | grep -v terminated | grep INSTANCE | awk '{print $2}'" %(r.region,name), capture=True)
        local('zabbix_api/remove_host.py %s %s' %(r.zserver,name))
        local('/usr/bin/ldapdelete -x -w %s -D "cn=admin,dc=social,dc=local" -h %s cn=%s,ou=hosts,dc=social,dc=local' %(r.secret,r.ldap,name))
        execute(puppet.puppetca_clean,name+'.social.local',host=r.puppetmaster)
        ip = local("host "+name+".asskickery.us | awk '{print $4}'", capture=True)
        local('. ../conf/awsdeploy.bashrc; /usr/local/bin/route53 del_record Z4512UDZ56AKC '+name+'.asskickery.us. A '+ip)
        local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-terminate-instances --region %s %s' %(r.region,instance))

def remove_west_ec2_instance(name, region='us-west-1'):
    r=config.get_devqa_west_conf()
    authinfo = config.auth()
    env.user = authinfo['user']
    env.key_filename = authinfo['key_filename']
    env.warn_only = True
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        instance = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-describe-instances --region %s --filter tag:Name=%s | grep -v terminated | grep INSTANCE | awk '{print $2}'" %(region,name), capture=True)
        local('/usr/bin/ldapdelete -x -w %s -D "cn=admin,dc=manhattan,dc=dev" -h %s cn=%s,ou=hosts,dc=manhattan,dc=dev' %(r.secret,r.ldap,name))
        execute(puppet.puppetca_clean,name+'.ecollegeqa.net',host=r.puppetmaster)
        ip = local("host "+name+".asskickery.us | awk '{print $4}'", capture=True)
        local('. ../conf/awsdeploy.bashrc; /usr/local/bin/route53 del_record Z4512UDZ56AKC '+name+'.asskickery.us. A '+ip)
        local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-terminate-instances --region %s %s' %(region,instance))

####
# File System Related tasks
####

@task
def setup_ten_drive_mirror():
    env.warn_only = True
    sudo('puppet agent -t')
    env.warn_only = True
    sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
    sudo('mdadm --create --force --assume-clean -R /dev/md0 -l0 --chunk=256 --raid-devices=10 /dev/xvdf /dev/xvdg /dev/xvdh /dev/xvdi /dev/xvdj /dev/xvdk /dev/xvdl /dev/xvdm /dev/xvdn /dev/xvdo')
    sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
    sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
    sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
    env.warn_only = False
    sudo('mdadm --create --force --assume-clean -R /dev/md0 -l0 --chunk=256 --raid-devices=10 /dev/xvdf /dev/xvdg /dev/xvdh /dev/xvdi /dev/xvdj /dev/xvdk /dev/xvdl /dev/xvdm /dev/xvdn /dev/xvdo')
    sudo('echo "`mdadm --detail --scan`" | tee -a /etc/mdadm.conf')
    sudo('blockdev --setra 128 /dev/md0')
    sudo('blockdev --setra 128 /dev/xvdf')
    sudo('blockdev --setra 128 /dev/xvdg')
    sudo('blockdev --setra 128 /dev/xvdh')
    sudo('blockdev --setra 128 /dev/xvdi')
    sudo('blockdev --setra 128 /dev/xvdj')
    sudo('blockdev --setra 128 /dev/xvdk')
    sudo('blockdev --setra 128 /dev/xvdl')
    sudo('blockdev --setra 128 /dev/xvdm')
    sudo('blockdev --setra 128 /dev/xvdn')
    sudo('blockdev --setra 128 /dev/xvdo')
    sudo('dd if=/dev/urandom of=/etc/data.key bs=1 count=32')
    time.sleep(5)
    sudo('cat /etc/data.key | cryptsetup luksFormat /dev/md0')
    sudo('cat /etc/data.key | cryptsetup luksOpen /dev/md0 data')

@task
def setup_four_drive_mirror():
    env.warn_only = True
    sudo('puppet agent -t')
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

def setup_two_drive_mirror():
    env.warn_only = True
    sudo('puppet agent -t')
    env.warn_only = True
    sudo("for i in `cat /proc/mdstat | grep md | awk '{print $1}'`; do mdadm --stop /dev/$i; done")
    sudo('mdadm --create --force --assume-clean -R /dev/md0 -l10 --chunk=256 --raid-devices=4 /dev/xvdf /dev/xvdg')
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

def setup_mongodb_lvm():
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

def setup_gluster_lvm():
    sudo('pvcreate /dev/mapper/data')
    sudo('vgcreate datavg /dev/mapper/data')
    sudo('lvcreate -l 100%vg -n datalv datavg')
    sudo('mke2fs -t ext4 -F /dev/datavg/datalv')
    sudo('echo "/dev/datavg/datalv  /data   ext4    defaults,auto,noatime,noexec    0       0" | tee -a /etc/fstab')
    sudo('mkdir -p /data/')
    sudo('mount -a')

def setup_rabbit_lvm():
    sudo('pvcreate /dev/mapper/data')
    sudo('vgcreate datavg /dev/mapper/data')
    sudo('lvcreate -l 100%vg -n datalv datavg')
    sudo('mke2fs -t ext4 -F /dev/datavg/datalv')
    sudo('echo "/dev/datavg/datalv  /data   ext4    defaults,auto,noatime,noexec    0       0" | tee -a /etc/fstab')
    sudo('mkdir -p /data/')
    sudo('mount -a')
    sudo('chown -R rabbitmq:rabbitmq /data/')
    sudo('service rabbitmq-server stop')
    sudo('rm -rf /var/lib/rabbitmq/')
    sudo('ln -s ln -s /data/ /var/lib/rabbitmq')
    sudo('service rabbitmq-server start')

####
# Generic Deploy 5 Nodes with 4 Raid 0 EBS Volumes
####

def deploy_one_node_with_10_ebs_io_volumes_raid_0(az,appname,puppetClass,iops='yes',capacity='100',size='m1.xlarge'):
    r=config.get_conf(az)
    ip_rid = third_party_generic_deployment(appname=appname,puppetClass=puppetClass,az=az,size=size,dmz='pri')
    rid = ip_rid['rid']
    ip = ip_rid['ip']
    time.sleep(120)
    for lun in ['/dev/sdf', '/dev/sdg', '/dev/sdh', '/dev/sdi', '/dev/sdj', '/dev/sdk', '/dev/sdl', '/dev/sdm', '/dev/sdn', '/dev/sdo']:
        ebs_vol = create_ebs_volume(az=az,iops=iops,size=capacity)
        attach_ebs_volume(device=lun, ebs_vol=ebs_vol, rid=rid, region=r.region)
    time.sleep(300)
    env.parallel = True
    execute(setup_ten_drive_mirror, host=ip)
    return ip

def deploy_five_nodes_with_4_ebs_volumes_raid_0(az,appname,puppetClass,size='m1.xlarge'):
    r=config.get_conf(az)
    iplist = []
    if az in ['use1a', 'use1c', 'use1d']:
        for azloop in ['use1a', 'use1a', 'use1c', 'use1c', 'use1d']:
            ip_rid = third_party_generic_deployment(appname=appname,puppetClass=puppetClass,az=azloop,size=size,dmz='pri')
            rid = ip_rid['rid']
            ip = ip_rid['ip']
            iplist.append(ip) 
            time.sleep(120)
            for lun in ['/dev/sdf', '/dev/sdg', '/dev/sdh', '/dev/sdi']:
                ebs_vol = create_ebs_volume(az=azloop)
                attach_ebs_volume(device=lun, ebs_vol=ebs_vol, rid=rid, region=r.region)
    if az in ['usw2a', 'usw2b', 'usw2c']:
        for azloop in ['usw2a', 'usw2a', 'usw2b', 'usw2b', 'usw2c']:
            ip_rid = third_party_generic_deployment(appname=appname,puppetClass=puppetClass,az=azloop,size=size,dmz='pri')
            rid = ip_rid['rid']
            ip = ip_rid['ip']
            iplist.append(ip)
            time.sleep(120)
            for lun in ['/dev/sdf', '/dev/sdg', '/dev/sdh', '/dev/sdi']:
                ebs_vol = create_ebs_volume(az=azloop)
                attach_ebs_volume(device=lun, ebs_vol=ebs_vol, rid=rid, region=r.region)
    time.sleep(300)
    env.parallel = True
    execute(setup_four_drive_mirror, hosts=iplist)
    return iplist

def deploy_three_nodes_with_2_ebs_volumes_raid_0(az,appname,puppetClass,iops='no',capacity='50',size='m1.medium'):
    r=config.get_conf(az)
    iplist = []
    if az in ['use1a', 'use1c', 'use1d']:
        for azloop in ['use1a', 'use1c', 'use1d']:
            ip_rid = third_party_generic_deployment(appname=appname,puppetClass=puppetClass,az=azloop,size=size,dmz='pri')
            rid = ip_rid['rid']
            ip = ip_rid['ip']
            iplist.append(ip)
            time.sleep(120)
            for lun in ['/dev/sdf', '/dev/sdg']:
                ebs_vol = create_ebs_volume(az=azloop,iops=iops,size=capacity)
                attach_ebs_volume(device=lun, ebs_vol=ebs_vol, rid=rid, region=r.region)
    if az in ['usw2a', 'usw2b', 'usw2c']:
        for azloop in ['usw2a', 'usw2b', 'usw2c']:
            ip_rid = third_party_generic_deployment(appname=appname,puppetClass=puppetClass,az=azloop,size=size,dmz='pri')
            rid = ip_rid['rid']
            ip = ip_rid['ip']
            iplist.append(ip)
            time.sleep(120)
            for lun in ['/dev/sdf', '/dev/sdg', '/dev/sdh', '/dev/sdi']:
                ebs_vol = create_ebs_volume(az=azloop,iops=iops,size=capacity)
                attach_ebs_volume(device=lun, ebs_vol=ebs_vol, rid=rid, region=r.region)
    time.sleep(300)
    env.parallel = True
    execute(setup_two_drive_mirror, hosts=iplist)
    return iplist

####
# Mongo Related Tasks
####

def deploy_five_node_mongodb_replica_set(az, shard='1', setname='mongo', app='sl'):
    env.warn_only = False
    r=config.get_conf(az)
    shardnum = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=%s-pri-%s-mongodb-s%s* | grep cn: | awk '{print $2}' | awk -F- '{print $5}'| tail -1" %(r.secret,r.admin,r.basedn,r.basedn,r.ldap,az,app,shard), capture=True)
    if shardnum:
        print (red("PROBLEM: Shard '%s' Already Exists")%(shard))
        sys.exit(0)
    appname = app+'-mongodb-s'+shard
    iplist = deploy_five_nodes_with_4_ebs_volumes_raid_0(az=az,appname=appname,puppetClass='mongodb')
    execute(setup_mongodb_lvm, hosts=iplist)
    execute(mongod.start, hosts=iplist)
    time.sleep(180)
    execute(mongod.create_five_node_mongo_cluster,host=iplist[0],setname=setname,node1=iplist[0],node2=iplist[1],node3=iplist[2],node4=iplist[3],node5=iplist[4])

def deploy_three_node_mongodb_replica_set(az, shard='1', setname='mongo', app='inf'):
    env.warn_only = False
    r=config.get_conf(az)
    shardnum = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=%s-pri-%s-mongodb-s%s* | grep cn: | awk '{print $2}' | awk -F- '{print $5}'| tail -1" %(r.secret,r.admin,r.basedn,r.basedn,r.ldap,az,app,shard), capture=True)
    if shardnum:
        print (red("PROBLEM: Shard '%s' Already Exists")%(shard))
        sys.exit(0)
    appname = app+'-mongodb-s'+shard
    iplist = deploy_three_nodes_with_2_ebs_volumes_raid_0(az=az,appname=appname,puppetClass='mongodb')
    execute(setup_mongodb_lvm, hosts=iplist)
    execute(mongod.start, hosts=iplist)
    time.sleep(180)
    execute(mongod.create_three_node_mongo_cluster,host=iplist[0],setname=setname,node1=iplist[0],node2=iplist[1],node3=iplist[2])

####
# Gluster Related Tasks
####

def deploy_five_node_gluster_cluster(az,app):
    env.warn_only = False
    appname = app+'-gluster'
    iplist = deploy_five_nodes_with_4_ebs_volumes_raid_0(az=az,appname=appname,puppetClass='gluster')
    execute(setup_gluster_lvm, hosts=iplist)


def main():
    print "This is a python module and should be run as such"

if __name__ == "__main__":
    main()
