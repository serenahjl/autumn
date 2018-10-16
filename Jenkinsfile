#!/usr/bin/env groovy Jenkinsfile

pipeline {
    agent none
    triggers {
        pollSCM('* * * * *')
    }
    stages {
        stage('env init') {
            when {
                branch 'dev'
            }
            agent {
                label 'master'
            }
            steps {
                sh '''
                    if [ -n "`docker ps -a | grep promise-spiderman-ci`" ]; then docker rm -f promise-spiderman-ci; fi
                    docker run -d --name=promise-spiderman-ci --hostname=promise-spiderman-ci -v /etc/localtime:/etc/localtime:ro -e "PYTHONPATH=/apps/svr/promise-spiderman" -e "ANSIBLE_CONFIG=/apps/svr/promise-spiderman/env.conf/ansible.cfg" -e "PYTHONOPTIMIZE=1" 172.40.224.7:5000/promise-back:v2.0
                '''
            }
        }
        stage('pull package') {
            when {
                branch 'dev'
            }
            agent {
                label 'master'
            }
            steps {
                sh '''
                    docker exec promise-spiderman-ci git clone -b dev http://192.168.182.51/promise/promise-spiderman.git /apps/svr/promise-spiderman
                    docker exec promise-spiderman-ci rm -rf /root/.pip/pip.conf
                    docker exec promise-spiderman-ci cp /apps/svr/promise-spiderman/env.conf/pip.conf /root/.pip/
                    docker exec promise-spiderman-ci cp -r /apps/svr/promise-spiderman/env.conf/ci-instance /apps/svr/promise-spiderman/instance
                '''
            }
        }
        stage('dependencies install') {
            when {
                branch 'dev'
            }
            agent {
                label 'master'
            }
            steps {
                sh '''
                    docker exec promise-spiderman-ci pip install --upgrade pip
                    docker exec promise-spiderman-ci pip install -r /apps/svr/promise-spiderman/requirements.txt
                    docker exec promise-spiderman-ci pip install git+http://192.168.182.51/promise/promise-gryphon.git
                    docker exec promise-spiderman-ci rm -rf /etc/yum.repos.d/el7_new.repo
                    docker exec promise-spiderman-ci cp /apps/svr/promise-spiderman/env.conf/BCLinux-Base.repo /etc/yum.repos.d/
                    docker exec promise-spiderman-ci cp /apps/svr/promise-spiderman/env.conf/BCLinux-Source.repo /etc/yum.repos.d/
                    docker exec promise-spiderman-ci cp /apps/svr/promise-spiderman/env.conf/BigCloud.repo /etc/yum.repos.d/
                    docker exec promise-spiderman-ci su -c "echo 223.105.0.149 mirrors.bclinux.org >> /etc/hosts"
                    docker exec promise-spiderman-ci su -c "echo 13.250.177.223 github.com >> /etc/hosts"
                    docker exec promise-spiderman-ci yum update nss curl -y
                    docker exec promise-spiderman-ci pip install git+https://github.com/tecstack/forward.git@develop
                '''
            }
        }
        stage('code check && unit test') {
            when {
                branch 'dev'
            }
            agent {
                label 'master'
            }
            steps {
                sh '''
                    docker exec promise-spiderman-ci flake8 /apps/svr/promise-spiderman --config=/apps/svr/promise-spiderman/tox.ini
                    docker exec promise-spiderman-ci nosetests -c /apps/svr/promise-spiderman/nosetests.ini
                    docker cp promise-spiderman-ci:/apps/svr/promise-spiderman/nosetests.xml $WORKSPACE
                    docker cp promise-spiderman-ci:/apps/svr/promise-spiderman/coverage.xml $WORKSPACE
                '''
            }
            post {
                always {
                    junit 'nosetests.xml'
		            step([
		                $class: 'CoberturaPublisher', autoUpdateHealth: false,
		                autoUpdateStability: false, coberturaReportFile: 'coverage.xml',
		                failUnhealthy: false, failUnstable: false, maxNumberOfBuilds: 0,
		                onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false])
		            cleanWs()
                }
                success {
                    sh '''
                        docker rm -f promise-spiderman-ci
                    '''
                }
                failure {
                    emailext body: '$DEFAULT_CONTENT', subject: '$DEFAULT_SUBJECT', to: 'linxiaosui@139.com'
                }
            }
        }

   }
   }