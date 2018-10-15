pipeline {
  agent none
  stages {
    stage('env init') {
      agent {
        node {
          label 'master'
        }
        
      }
      steps {
        sh '''if [ -n "`docker ps -a | grep promise-spiderman-ci`" ]; then docker rm -f promise-spiderman-ci; fi
                    docker run -d --name=promise-spiderman-ci --hostname=promise-spiderman-ci -v /etc/localtime:/etc/localtime:ro -e "PYTHONPATH=/apps/svr/promise-spiderman" -e "ANSIBLE_CONFIG=/apps/svr/promise-spiderman/env.conf/ansible.cfg" -e "PYTHONOPTIMIZE=1" 172.40.224.7:5000/promise-back:v2.0
'''
      }
    }
    stage('pull package') {
      steps {
        sh '''docker exec promise-spiderman-ci git clone -b dev http://192.168.182.51/promise/promise-spiderman.git /apps/svr/promise-spiderman
                    docker exec promise-spiderman-ci rm -rf /root/.pip/pip.conf
                    docker exec promise-spiderman-ci cp /apps/svr/promise-spiderman/env.conf/pip.conf /root/.pip/
                    docker exec promise-spiderman-ci cp -r /apps/svr/promise-spiderman/env.conf/ci-instance /apps/svr/promise-spiderman/instance'''
      }
    }
  }
}