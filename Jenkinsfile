pipeline {
  agent any
  stages {
    stage('env init') {
      steps {
        sh '''if [ -n "`docker ps -a | grep promise-spiderman-ci`" ]; then docker rm -f promise-spiderman-ci; fi
                    docker run -d --name=promise-spiderman-ci --hostname=promise-spiderman-ci -v /etc/localtime:/etc/localtime:ro -e "PYTHONPATH=/apps/svr/promise-spiderman" -e "ANSIBLE_CONFIG=/apps/svr/promise-spiderman/env.conf/ansible.cfg" -e "PYTHONOPTIMIZE=1" 172.40.224.7:5000/promise-back:v2.0
'''
      }
    }
  }
}