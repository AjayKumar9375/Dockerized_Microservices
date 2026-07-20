pipeline {
    agent {
        label 'my-docker-agent'
    }

    options {
        timestamps()
        ansiColor('xterm')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    parameters {
        string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Image tag to build, push, and deploy.')
        booleanParam(name: 'RUN_SONAR', defaultValue: true, description: 'Run SonarQube analysis.')
        booleanParam(name: 'PUSH_IMAGES', defaultValue: false, description: 'Push images to Docker Hub or ECR.')
        choice(name: 'REGISTRY_TYPE', choices: ['dockerhub', 'ecr'], description: 'Container registry.')
        string(name: 'REGISTRY_NAMESPACE', defaultValue: 'ajaykumar9375', description: 'Docker Hub namespace. Ignored for ECR.')
        booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: false, description: 'Deploy with Helm.')
        booleanParam(name: 'UPDATE_EKS_KUBECONFIG', defaultValue: false, description: 'Update kubeconfig for EKS before deploy.')
        string(name: 'AWS_REGION', defaultValue: 'us-east-1', description: 'AWS region for ECR/EKS.')
        string(name: 'AWS_ACCOUNT_ID', defaultValue: '', description: 'AWS account ID for ECR.')
        string(name: 'EKS_CLUSTER_NAME', defaultValue: '', description: 'EKS cluster name.')
        string(name: 'K8S_REPLICAS', defaultValue: '1', description: 'Replica count for Jenkins demo deployments.')
    }

    environment {
        APP_NAME = 'dockerized-microservices'
        BACKEND_IMAGE = 'dockerized-microservices-backend'
        FRONTEND_IMAGE = 'dockerized-microservices-frontend'
        K8S_NAMESPACE = 'dockerized-microservices'
        BACKEND_PORT = '18000'
        FRONTEND_PORT = '13000'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate') {
            steps {
                sh 'docker compose config --quiet'
            }
        }

        stage('Build Images') {
            steps {
                sh '''
                    docker build -t ${BACKEND_IMAGE}:latest -t ${BACKEND_IMAGE}:${IMAGE_TAG} ./backend
                    docker build -t ${FRONTEND_IMAGE}:latest -t ${FRONTEND_IMAGE}:${IMAGE_TAG} ./frontend
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    docker run --rm --user root ${BACKEND_IMAGE}:${IMAGE_TAG} python -m compileall app
                    docker run --rm ${BACKEND_IMAGE}:${IMAGE_TAG} python -c "from app.main import app; print(app.title)"
                '''
            }
        }

        stage('SonarQube') {
            when {
                expression { return params.RUN_SONAR }
            }
            steps {
                script {
                    def scannerHome = tool 'sonar-scanner'
                    withSonarQubeEnv('sonar-server') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        stage('Docker Evidence') {
            steps {
                sh '''
                    mkdir -p pipeline-evidence

                    BACKEND_PORT=${BACKEND_PORT} FRONTEND_PORT=${FRONTEND_PORT} docker compose up -d --no-build

                    for attempt in $(seq 1 12); do
                      if health=$(docker compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read().decode())"); then
                        echo "$health" | tee pipeline-evidence/backend-health.json
                        break
                      fi
                      echo "Waiting for backend health check (${attempt}/12)"
                      sleep 5
                    done

                    docker images --format "table {{.Repository}}\\t{{.Tag}}\\t{{.ID}}\\t{{.Size}}\\t{{.CreatedSince}}" \
                      | tee pipeline-evidence/docker-images.txt
                    docker compose ps | tee pipeline-evidence/docker-compose-ps.txt
                    docker ps --filter "name=dmd-" --format "table {{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}" \
                      | tee pipeline-evidence/docker-containers.txt

                    test -s pipeline-evidence/backend-health.json
                '''
            }
        }

        stage('Push Images') {
            when {
                expression { return params.PUSH_IMAGES }
            }
            steps {
                script {
                    def registry = params.REGISTRY_NAMESPACE

                    if (params.REGISTRY_TYPE == 'ecr') {
                        if (!params.AWS_ACCOUNT_ID?.trim()) {
                            error('AWS_ACCOUNT_ID is required when REGISTRY_TYPE=ecr')
                        }
                        registry = "${params.AWS_ACCOUNT_ID}.dkr.ecr.${params.AWS_REGION}.amazonaws.com"
                        sh "aws ecr get-login-password --region ${params.AWS_REGION} | docker login --username AWS --password-stdin ${registry}"
                    }

                    sh """
                        docker tag ${env.BACKEND_IMAGE}:${params.IMAGE_TAG} ${registry}/${env.BACKEND_IMAGE}:${params.IMAGE_TAG}
                        docker tag ${env.FRONTEND_IMAGE}:${params.IMAGE_TAG} ${registry}/${env.FRONTEND_IMAGE}:${params.IMAGE_TAG}
                        docker push ${registry}/${env.BACKEND_IMAGE}:${params.IMAGE_TAG}
                        docker push ${registry}/${env.FRONTEND_IMAGE}:${params.IMAGE_TAG}

                        {
                          echo "${registry}/${env.BACKEND_IMAGE}:${params.IMAGE_TAG}"
                          echo "${registry}/${env.FRONTEND_IMAGE}:${params.IMAGE_TAG}"
                        } | tee pipeline-evidence/pushed-images.txt
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            when {
                expression { return params.DEPLOY_TO_K8S }
            }
            steps {
                script {
                    if (params.UPDATE_EKS_KUBECONFIG) {
                        if (!params.EKS_CLUSTER_NAME?.trim()) {
                            error('EKS_CLUSTER_NAME is required when UPDATE_EKS_KUBECONFIG=true')
                        }
                        sh "aws eks update-kubeconfig --region ${params.AWS_REGION} --name ${params.EKS_CLUSTER_NAME}"
                    }

                    def backendRepository = env.BACKEND_IMAGE
                    def frontendRepository = env.FRONTEND_IMAGE

                    if (params.PUSH_IMAGES) {
                        def registry = params.REGISTRY_TYPE == 'ecr'
                            ? "${params.AWS_ACCOUNT_ID}.dkr.ecr.${params.AWS_REGION}.amazonaws.com"
                            : params.REGISTRY_NAMESPACE
                        backendRepository = "${registry}/${env.BACKEND_IMAGE}"
                        frontendRepository = "${registry}/${env.FRONTEND_IMAGE}"
                    }

                    catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                        sh """
                            kubectl get nodes
                            helm upgrade --install ${env.APP_NAME} ./helm/dockerized-microservices \
                              --namespace ${env.K8S_NAMESPACE} \
                              --create-namespace \
                              --set backend.image.repository=${backendRepository} \
                              --set frontend.image.repository=${frontendRepository} \
                              --set backend.image.tag=${params.IMAGE_TAG} \
                              --set frontend.image.tag=${params.IMAGE_TAG} \
                              --set backend.replicaCount=${params.K8S_REPLICAS} \
                              --set frontend.replicaCount=${params.K8S_REPLICAS} \
                              --wait \
                              --timeout 5m
                        """
                    }
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

                    kubectl -n ${K8S_NAMESPACE} get pods -o wide | tee pipeline-evidence/kubernetes-pods.txt
                    kubectl -n ${K8S_NAMESPACE} get svc -o wide | tee pipeline-evidence/kubernetes-services.txt
                    kubectl -n ${K8S_NAMESPACE} get ingress -o wide | tee pipeline-evidence/kubernetes-ingress.txt || true
                    kubectl -n ${K8S_NAMESPACE} get events --sort-by=.lastTimestamp \
                      | tail -n 40 | tee pipeline-evidence/kubernetes-events.txt || true
                    kubectl -n ${K8S_NAMESPACE} logs deployment/backend --tail=80 \
                      | tee pipeline-evidence/backend-logs.txt || true
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'pipeline-evidence/**', allowEmptyArchive: true
            sh 'docker compose down --remove-orphans || true'
        }
    }
}
