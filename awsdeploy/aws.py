#!/usr/bin/python
# vim: set expandtab:
from fabric.api import *
from fabric.operations import local,put
from fabric.colors import *

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
        return ip


def deploy_west_ec2_ami(name, puppetClass, size='m1.small'):
    r=get_west_conf()
    deploy_ec2_ami (name, puppetClass, r.ami, size, r.zone, r.region, r.basedn, r.ldap, r.secret, r.subnet, r.sgroup, r.domain, r.puppetmaster)

def main():
    print "This is a python module and should be run as such"

if __name__ == "__main__":
    main()
