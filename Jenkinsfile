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
                    if [ -n "`docker ps -a | grep promise-autumn-ci`" ]; then docker rm -f promise-autumn-ci; fi
                    docker run -d --name=promise-autumn-ci --hostname=promise-autumn-ci -v /etc/localtime:/etc/localtime:ro -e "PYTHONPATH=/apps/svr/promise-autumn" -e "ANSIBLE_CONFIG=/apps/svr/promise-autumn/env.conf/ansible.cfg" -e "PYTHONOPTIMIZE=1" 172.40.224.7:5000/promise-back:v2.0
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
                    docker exec promise-autumn-ci git clone -b dev http://192.168.182.51/huangjinglin/autumn.git /apps/svr/promise-autumn
                    docker exec promise-autumn-ci rm -rf /root/.pip/pip.conf
                    docker exec promise-autumn-ci cp /apps/svr/promise-autumn/env.conf/pip.conf /root/.pip/
                    docker exec promise-autumn-ci cp -r /apps/svr/promise-autumn/env.conf/ci-instance /apps/svr/promise-autumn/instance
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
                    docker exec promise-autumn-ci pip install --upgrade pip
                    docker exec promise-autumn-ci pip install -r /apps/svr/promise-autumn/requirements.txt
                    docker exec promise-autumn-ci pip show requests
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
                    docker exec promise-autumn-ci flake8 /apps/svr/promise-autumn --config=/apps/svr/promise-autumn/tox.ini
                    docker exec promise-autumn-ci nosetests -c /apps/svr/promise-autumn/nosetests.ini
                    docker cp promise-autumn-ci:/apps/svr/promise-autumn/nosetests.xml $WORKSPACE
                    docker cp promise-autumn-ci:/apps/svr/promise-autumn/coverage.xml $WORKSPACE
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
                        docker rm -f promise-autumn-ci
                    '''
                }
                failure {
                    emailext body: '$DEFAULT_CONTENT', subject: '$DEFAULT_SUBJECT', to: 'huangjinglin@gd.chinamobile.com'
                }
            }
        }

   }
   }