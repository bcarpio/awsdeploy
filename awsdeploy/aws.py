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

####
# This Task Does The Following
# * Checks LDAP For Existing Node
# * Creates EC2 Instance
# * Dynamically Generates A user-data script which names the node
# * Tags The Node With The Host Name
# * Updates LDAP With The Nodename And IP
# * Adds The Node To Route 53
####

def deploy_ec2_ami(name, ami, size, zone, region, basedn, ldap, secret, subnet, sgroup, domain, puppetmaster, admin):
    with settings(
        hide('running', 'stdout')
    ):
        if "." in name:
            name = name.replace('.','x')
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
            local('cat ../templates/template.ldif | sed -e s/HOST/\'%s\'/g -e s/IP/\'%s\'/g -e s/BASEDN/%s/g | ldapadd -x -w %s -D "%s" -h %s' %(name,ip,basedn,secret,admin+basedn,ldap))
            local('. ../conf/awsdeploy.bashrc; /usr/local/bin/route53 add_record Z4512UDZ56AKC '+name+'.asskickery.us A '+ip)
            local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-create-tags %s --region %s --tag Name=%s' %(rid,region,name))
            local('rm ../tmp/user-data.sh')
            local('rm ../tmp/ec2-run-instances.out')
            print (blue("SUCCESS: Node '%s' Deployed To %s")%(name,region))
            local('echo %s >> ../tmp/ip.out' %(ip))
    return {'ip' : ip, 'rid' : rid}

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

####
# EC2 Storage Tasks
####

def create_ebs_volume(az,size='50',region='east'):
    if region == 'east':
        r=config.get_prod_east_conf()
    if region == 'west':
        r=config.get_devqa_west_conf
    if az == 'use1a':
        zone = 'us-east-1a'
    elif az == 'use1c':
        zone = 'us-east-1c'
    elif az == 'use1d':
        zone = 'us-east-1d'
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        ebs_vol = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-create-volume --region %s --size %s --availability-zone %s | awk '{print $2}'" %(r.region, size, zone), capture=True)
    return ebs_vol

def attach_ebs_volume(device, ebs_vol, rid, region):
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-attach-volume %s --region %s -i %s -d %s' %(ebs_vol,region,rid,device))

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
    r=config.get_conf(az)
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        local("sed -e s/HOST/%s/g -e s/PUPPETCLASS/%s/g -e s/BASEDN/%s/g ../templates/modify.ldif | /usr/bin/ldapmodify -v -x -w %s -D %s%s -h %s" %(hostname,puppetClass,r.basedn,r.secret,r.admin,r.basedn,r.ldap))


### 
# This the generic application deployment task
###
def app_deploy_generic(appname, version, az, count='1', puppetClass='nodejs', size='m1.small'):
    cleanup()
    r=config.get_conf(az)
    authinfo = config.auth()
    env.user = authinfo['user']
    env.key_filename = authinfo['key_filename']
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
        if az == 'dev':
            ip_rid = deploy_west_ec2_ami(name=name,size=size)
        if az == 'qa':
            ip_rid = deploy_west_ec2_ami(name=name,size=size)
    elif dmz == 'pub':
        if az == 'use1a':
            ip_rid = deploy_east_1a_public_1(name=name,size=size)
        if az == 'use1c':
            ip_rid = deploy_east_1c_public_3(name=name,size=size)
    else:
        print "ERROR: Wrong dmz specified"

    if isinstance(puppetClass, basestring):
        ldap_modify(hostname=name, puppetClass=puppetClass, az=az)
    else:
        for pclass in puppetClass:
            ldap_modify(hostname=name, puppetClass=pclass, az=az)
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

def remove_east_ec2_instance(name, region='us-east-1'):
    r=config.get_prod_east_conf()
    authinfo = config.auth()
    env.user = authinfo['user']
    env.key_filename = authinfo['key_filename']
    env.warn_only = True
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        instance = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-describe-instances --region %s --filter tag:Name=%s | grep -v terminated | grep INSTANCE | awk '{print $2}'" %(region,name), capture=True)
        local('zabbix_api/remove_host.py %s' %(name))
        local('/usr/bin/ldapdelete -x -w %s -D "cn=admin,dc=social,dc=local" -h %s cn=%s,ou=hosts,dc=social,dc=local' %(r.secret,r.ldap,name))
        execute(puppet.puppetca_clean,name+'.social.local',host='10.201.2.10')
        ip = local("host "+name+".asskickery.us | awk '{print $4}'", capture=True)
        local('. ../conf/awsdeploy.bashrc; /usr/local/bin/route53 del_record Z4512UDZ56AKC '+name+'.asskickery.us. A '+ip)
        local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-terminate-instances --region %s %s' %(region,instance))

def remove_west_ec2_instance(name, region='us-west-1'):
    r=config.get_devqa_west_conf()
    authinfo = config.auth()
    env.user = authinfo['user']
    env.key_filename = authinfo['key_filename']
    env.warn_only = True
    with lcd(os.path.join(os.path.dirname(__file__),'.')):
        instance = local(". ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-describe-instances --region %s --filter tag:Name=%s | grep -v terminated | grep INSTANCE | awk '{print $2}'" %(region,name), capture=True)
        local('/usr/bin/ldapdelete -x -w %s -D "cn=admin,dc=manhattan,dc=dev" -h %s cn=%s,ou=hosts,dc=manhattan,dc=dev' %(r.secret,r.ldap,name))
        execute(puppet.puppetca_clean,name+'.ecollegeqa.net',host='10.52.74.38')
        ip = local("host "+name+".asskickery.us | awk '{print $4}'", capture=True)
        local('. ../conf/awsdeploy.bashrc; /usr/local/bin/route53 del_record Z4512UDZ56AKC '+name+'.asskickery.us. A '+ip)
        local('. ../conf/awsdeploy.bashrc; ../ec2-api-tools/bin/ec2-terminate-instances --region %s %s' %(region,instance))

####
# File System Related tasks
####

@task
def setup_four_drive_mirror():
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

def setup_two_drive_mirror():
    env.warn_only = True
    sudo('puppetd --test')
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

####
# Generic Deploy 5 Nodes with 4 Raid 0 EBS Volumes
####

def deploy_five_nodes_with_4_ebs_volumes_raid_0(appname,puppetClass,size='m1.xlarge'):
    r=config.get_prod_east_conf()
    iplist = []
    for az in ['use1a', 'use1a', 'use1c', 'use1c', 'use1d']:
        ip_rid = third_party_generic_deployment(appname=appname,puppetClass=puppetClass,az=az,size=size,dmz='pri')
        rid = ip_rid['rid']
        ip = ip_rid['ip']
        iplist.append(ip) 
        time.sleep(120)
        for lun in ['/dev/sdf', '/dev/sdg', '/dev/sdh', '/dev/sdi']:
            ebs_vol = create_ebs_volume(az=az)
            attach_ebs_volume(device=lun, ebs_vol=ebs_vol, rid=rid, region=r.region)
    time.sleep(300)
    env.parallel = True
    execute(setup_four_drive_mirror, hosts=iplist)
    return iplist

def deploy_three_nodes_with_2_ebs_volumes_raid_0(appname,puppetClass,size='m1.medium'):
    r=config.get_prod_east_conf()
    iplist = []
    for az in ['use1a', 'use1c', 'use1d']:
        ip_rid = third_party_generic_deployment(appname=appname,puppetClass=puppetClass,az=az,size=size,dmz='pri')
        rid = ip_rid['rid']
        ip = ip_rid['ip']
        iplist.append(ip)
        time.sleep(120)
        for lun in ['/dev/sdf', '/dev/sdg']:
            ebs_vol = create_ebs_volume(az=az)
            attach_ebs_volume(device=lun, ebs_vol=ebs_vol, rid=rid, region=r.region)
    time.sleep(300)
    env.parallel = True
    execute(setup_two_drive_mirror, hosts=iplist)
    return iplist

####
# Mongo Related Tasks
####

def deploy_five_node_mongodb_replica_set(shard='1', setname='mongo', app='sl'):
    env.warn_only = False
    r=config.get_prod_east_conf()
    shardnum = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=use1a-pri-%s-mongodb-s%s* | grep cn: | awk '{print $2}' | awk -F- '{print $5}'| tail -1" %(r.secret,r.admin,r.basedn,r.basedn,r.ldap,app,shard), capture=True)
    if shardnum:
        print (red("PROBLEM: Shard '%s' Already Exists")%(shard))
        sys.exit(0)
    appname = app+'-mongodb-s'+shard
    iplist = deploy_five_nodes_with_4_ebs_volumes_raid_0(appname=appname,puppetClass='mongodb')
    execute(setup_mongodb_lvm, hosts=iplist)
    execute(mongod.start, hosts=iplist)
    time.sleep(120)
    execute(mongod.create_five_node_mongo_cluster,host=iplist[0],setname=setname,node1=iplist[0],node2=iplist[1],node3=iplist[2],node4=iplist[3],node5=iplist[4])

def deploy_three_node_mongodb_replica_set(shard='1', setname='mongo', app='inf'):
    env.warn_only = False
    r=config.get_prod_east_conf()
    shardnum = local("/usr/bin/ldapsearch -x -w %s -D %s%s -b %s -h %s -LLL cn=use1a-pri-%s-mongodb-s%s* | grep cn: | awk '{print $2}' | awk -F- '{print $5}'| tail -1" %(r.secret,r.admin,r.basedn,r.basedn,r.ldap,app,shard), capture=True)
    if shardnum:
        print (red("PROBLEM: Shard '%s' Already Exists")%(shard))
        sys.exit(0)
    appname = app+'-mongodb-s'+shard
    iplist = deploy_three_nodes_with_2_ebs_volumes_raid_0(appname=appname,puppetClass='mongodb')
    execute(setup_mongodb_lvm, hosts=iplist)
    execute(mongod.start, hosts=iplist)
    time.sleep(120)
    execute(mongod.create_three_node_mongo_cluster,host=iplist[0],setname=setname,node1=iplist[0],node2=iplist[1],node3=iplist[2])

####
# Gluster Related Tasks
####

def deploy_five_node_gluster_cluster(app):
    env.warn_only = False
    appname = app+'-gluster'
    iplist = deploy_five_nodes_with_4_ebs_volumes_raid_0(appname=appname,puppetClass='gluster')
    execute(setup_gluster_lvm, hosts=iplist)


def main():
    print "This is a python module and should be run as such"

if __name__ == "__main__":
    main()
