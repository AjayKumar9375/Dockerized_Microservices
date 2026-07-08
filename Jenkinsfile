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
        booleanParam(name: 'UPDATE_EKS_KUBECONFIG', defaultValue: false, description: 'Run aws eks update-kubeconfig before Kubernetes deployment.')
        choice(name: 'REGISTRY_TYPE', choices: ['dockerhub', 'ecr'], description: 'Container registry target.')
        string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag to build and optionally push.')
        string(name: 'JENKINS_BACKEND_PORT', defaultValue: '18000', description: 'Temporary backend port used only for Jenkins Docker evidence.')
        string(name: 'JENKINS_FRONTEND_PORT', defaultValue: '13000', description: 'Temporary frontend port used only for Jenkins Docker evidence.')
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
                sh 'docker compose config --quiet'
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
                        def scannerHome = tool 'sonar-scanner'

                withSonarQubeEnv('sonar-server') {
                    sh "${scannerHome}/bin/sonar-scanner"
                }
                    } catch (err) {
                        echo "SonarQube is not configured on this Jenkins controller yet: ${err}"
                        echo 'Install SonarQube Scanner and configure a server named "sonar-server" to run this stage fully.'
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

        stage('Docker Evidence') {
            steps {
                sh '''
                    mkdir -p pipeline-evidence

                    echo "========== DOCKER IMAGES =========="
                    docker images --format "table {{.Repository}}\\t{{.Tag}}\\t{{.ID}}\\t{{.Size}}\\t{{.CreatedSince}}" \
                      | tee pipeline-evidence/docker-images.txt

                    echo "========== START DOCKER COMPOSE STACK =========="
                    BACKEND_PORT=${JENKINS_BACKEND_PORT} FRONTEND_PORT=${JENKINS_FRONTEND_PORT} docker compose up -d --no-build
                    sleep 15

                    echo "========== DOCKER COMPOSE SERVICES =========="
                    docker compose ps | tee pipeline-evidence/docker-compose-ps.txt

                    echo "========== RUNNING PROJECT CONTAINERS =========="
                    docker ps --filter "name=dmd-" --format "table {{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}" \
                      | tee pipeline-evidence/docker-running-containers.txt

                    echo "========== BACKEND HEALTH CHECK =========="
                    curl -fsS http://localhost:${JENKINS_BACKEND_PORT}/health \
                      | tee pipeline-evidence/backend-health.json || true
                '''
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

        stage('Registry Evidence') {
            when {
                expression { return params.PUSH_IMAGES }
            }
            steps {
                script {
                    if (params.REGISTRY_TYPE == 'dockerhub') {
                        sh '''
                            mkdir -p pipeline-evidence

                            {
                              echo "Docker Hub backend image:"
                              echo "https://hub.docker.com/r/${DOCKERHUB_NAMESPACE}/${BACKEND_IMAGE}/tags"
                              echo
                              echo "Docker Hub frontend image:"
                              echo "https://hub.docker.com/r/${DOCKERHUB_NAMESPACE}/${FRONTEND_IMAGE}/tags"
                              echo
                              echo "Local pushed tags:"
                              docker images --format "table {{.Repository}}\\t{{.Tag}}\\t{{.ID}}\\t{{.Size}}\\t{{.CreatedSince}}"
                            } | tee pipeline-evidence/registry-images.txt
                        '''
                    } else {
                        sh '''
                            mkdir -p pipeline-evidence

                            echo "========== ECR BACKEND IMAGES =========="
                            aws ecr describe-images \
                              --repository-name ${BACKEND_IMAGE} \
                              --region ${AWS_REGION} \
                              --query "imageDetails[].{Tags:imageTags,PushedAt:imagePushedAt,Size:imageSizeInBytes}" \
                              --output table | tee pipeline-evidence/ecr-backend-images.txt

                            echo "========== ECR FRONTEND IMAGES =========="
                            aws ecr describe-images \
                              --repository-name ${FRONTEND_IMAGE} \
                              --region ${AWS_REGION} \
                              --query "imageDetails[].{Tags:imageTags,PushedAt:imagePushedAt,Size:imageSizeInBytes}" \
                              --output table | tee pipeline-evidence/ecr-frontend-images.txt
                        '''
                    }
                }
            }
        }

        stage('Prepare Kubernetes Context') {
            when {
                allOf {
                    expression { return params.DEPLOY_TO_K8S }
                    expression { return params.UPDATE_EKS_KUBECONFIG }
                }
            }
            steps {
                sh '''
                    aws eks update-kubeconfig --region ${AWS_REGION} --name ${EKS_CLUSTER_NAME}
                    kubectl config current-context
                    kubectl get nodes
                '''
            }
        }

        stage('Deploy to Kubernetes') {
            when {
                expression { return params.DEPLOY_TO_K8S }
            }
            steps {
                script {
                    def backendRepository = env.BACKEND_IMAGE
                    def frontendRepository = env.FRONTEND_IMAGE

                    if (params.PUSH_IMAGES && params.REGISTRY_TYPE == 'dockerhub') {
                        backendRepository = "${env.DOCKERHUB_NAMESPACE}/${env.BACKEND_IMAGE}"
                        frontendRepository = "${env.DOCKERHUB_NAMESPACE}/${env.FRONTEND_IMAGE}"
                    }

                    if (params.PUSH_IMAGES && params.REGISTRY_TYPE == 'ecr') {
                        backendRepository = "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com/${env.BACKEND_IMAGE}"
                        frontendRepository = "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com/${env.FRONTEND_IMAGE}"
                    }

                    sh """
                        kubectl get nodes
                        helm upgrade --install ${env.APP_NAME} ./helm/dockerized-microservices \
                          --namespace ${env.K8S_NAMESPACE} \
                          --create-namespace \
                          --set backend.image.repository=${backendRepository} \
                          --set frontend.image.repository=${frontendRepository} \
                          --set backend.image.tag=${params.IMAGE_TAG} \
                          --set frontend.image.tag=${params.IMAGE_TAG}

                        kubectl -n ${env.K8S_NAMESPACE} rollout status deployment/backend --timeout=180s
                        kubectl -n ${env.K8S_NAMESPACE} rollout status deployment/frontend --timeout=180s
                    """
                }
            }
        }

        stage('Kubernetes Evidence') {
            when {
                expression { return params.DEPLOY_TO_K8S }
            }
            steps {
                sh '''
                    mkdir -p pipeline-evidence

                    echo "========== KUBERNETES PODS =========="
                    kubectl -n ${K8S_NAMESPACE} get pods -o wide \
                      | tee pipeline-evidence/kubernetes-pods.txt

                    echo "========== KUBERNETES SERVICES =========="
                    kubectl -n ${K8S_NAMESPACE} get svc -o wide \
                      | tee pipeline-evidence/kubernetes-services.txt

                    echo "========== KUBERNETES DEPLOYMENTS =========="
                    kubectl -n ${K8S_NAMESPACE} get deployments -o wide \
                      | tee pipeline-evidence/kubernetes-deployments.txt

                    echo "========== KUBERNETES INGRESS =========="
                    kubectl -n ${K8S_NAMESPACE} get ingress -o wide \
                      | tee pipeline-evidence/kubernetes-ingress.txt || true
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'pipeline-evidence/**', allowEmptyArchive: true
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
