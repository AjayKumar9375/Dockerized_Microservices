pipeline {
    agent {
        label 'my-docker-agent'
    }

    options {
        timestamps()
        ansiColor('xterm')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    parameters {
        booleanParam(name: 'PUSH_IMAGES', defaultValue: false, description: 'Push Docker images to Docker Hub or AWS ECR.')
        booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: false, description: 'Deploy the app to the current Kubernetes context using Helm.')
        choice(name: 'REGISTRY_TYPE', choices: ['dockerhub', 'ecr'], description: 'Container registry target.')
        string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag to build and optionally push.')
    }

    environment {
        APP_NAME = 'dockerized-microservices'
        BACKEND_IMAGE = 'dockerized-microservices-backend'
        FRONTEND_IMAGE = 'dockerized-microservices-frontend'
        DOCKERHUB_NAMESPACE = 'ajaykumar9375'
        AWS_REGION = 'us-east-1'
        AWS_ACCOUNT_ID = '141145000733'
        EKS_CLUSTER_NAME = 'confused-hiphop-crab'
        K8S_NAMESPACE = 'dockerized-microservices'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'docker compose config'
                sh 'docker compose build'
            }
        }

        stage('Test') {
            steps {
                sh 'docker run --rm --user root dockerized-microservices-backend:latest python -m compileall app'
                sh 'docker run --rm dockerized-microservices-backend:latest python -c "from app.main import app; print(app.title)"'
            }
        }

        stage('SonarQube Scan') {
            steps {
                script {
                    try {
                        withSonarQubeEnv('sonarqube') {
                            sh 'sonar-scanner'
                        }
                    } catch (err) {
                        echo "SonarQube is not configured on this Jenkins controller yet: ${err}"
                        echo 'Install SonarQube Scanner and configure a server named "sonarqube" to run this stage fully.'
                    }
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t ${BACKEND_IMAGE}:${IMAGE_TAG} ./backend'
                sh 'docker build -t ${FRONTEND_IMAGE}:${IMAGE_TAG} ./frontend'
            }
        }

        stage('Push Images') {
            when {
                expression { return params.PUSH_IMAGES }
            }
            steps {
                script {
                    if (params.REGISTRY_TYPE == 'dockerhub') {
                        sh '''
                            docker tag ${BACKEND_IMAGE}:${IMAGE_TAG} ${DOCKERHUB_NAMESPACE}/${BACKEND_IMAGE}:${IMAGE_TAG}
                            docker tag ${FRONTEND_IMAGE}:${IMAGE_TAG} ${DOCKERHUB_NAMESPACE}/${FRONTEND_IMAGE}:${IMAGE_TAG}
                            docker push ${DOCKERHUB_NAMESPACE}/${BACKEND_IMAGE}:${IMAGE_TAG}
                            docker push ${DOCKERHUB_NAMESPACE}/${FRONTEND_IMAGE}:${IMAGE_TAG}
                        '''
                    } else {
                        sh '''
                            aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
                            docker tag ${BACKEND_IMAGE}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_IMAGE}:${IMAGE_TAG}
                            docker tag ${FRONTEND_IMAGE}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${FRONTEND_IMAGE}:${IMAGE_TAG}
                            docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_IMAGE}:${IMAGE_TAG}
                            docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${FRONTEND_IMAGE}:${IMAGE_TAG}
                        '''
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                expression { return params.DEPLOY_TO_K8S }
            }
            steps {
                sh '''
                    kubectl get nodes
                    helm upgrade --install ${APP_NAME} ./helm/dockerized-microservices \
                      --namespace ${K8S_NAMESPACE} \
                      --create-namespace \
                      --set backend.image.tag=${IMAGE_TAG} \
                      --set frontend.image.tag=${IMAGE_TAG}
                '''
            }
        }
    }

    post {
        always {
            sh 'docker compose down --remove-orphans || true'
        }
        success {
            echo 'Pipeline completed successfully.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }
    }
}
