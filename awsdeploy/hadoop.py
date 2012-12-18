from fabric.api import *
from fabric.operations import local,put
import os

@task
def start_hadoop():
	run('su - hduser -c "/opt/hadoop/hadoop/bin/start-dfs.sh"')
	run('su - hduser -c "/opt/hadoop/hadoop/bin/start-mapred.sh"')

@task
def stop_hadoop():
	sudo('su - hduser -c "/opt/hadoop/hadoop/bin/stop-mapred.sh')
	sudo('su - hduser -c "/opt/hadoop/hadoop/bin/stop-dfs.sh')
