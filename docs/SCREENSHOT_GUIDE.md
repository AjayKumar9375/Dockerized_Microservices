# Portfolio Screenshot Guide

Use real screenshots from your own machine/cloud account. Save images in the `screenshots/` folder and reference them from the README.

## 1. Architecture Diagram

Open `docs/architecture.mmd` in one of these tools:

- GitHub README preview with a Mermaid code block
- https://mermaid.live
- diagrams.net, if you prefer a drag-and-drop diagram

Export or screenshot the diagram as:

```text
screenshots/architecture-diagram.png
```

Suggested diagram flow:

```text
GitHub -> Jenkins -> SonarQube -> Docker -> Docker Hub/AWS ECR -> Kubernetes/EKS -> App Services
```

## 2. Jenkins Pipeline Screenshot

Add this repository to Jenkins as a Pipeline job and point it to the root `Jenkinsfile`.

Minimum local screenshot:

1. Run the pipeline with default parameters.
2. Capture the Jenkins stage view showing:
   - Checkout
   - Build
   - Test
   - SonarQube Scan
   - Docker Build
   - Docker Evidence
   - Push Images
   - Registry Evidence
   - Prepare Kubernetes Context
   - Deploy to Kubernetes
   - Kubernetes Evidence

Save as:

```text
screenshots/jenkins-pipeline-stages.png
```

For a complete cloud deployment screenshot, configure:

- Docker on the Jenkins agent
- SonarQube server named `sonarqube`
- Docker Hub credentials or AWS credentials
- `kubectl` and `helm`
- A Kubernetes cluster or EKS cluster

Then rerun the pipeline with:

```text
PUSH_IMAGES=true
DEPLOY_TO_K8S=true
```

The Jenkinsfile creates `pipeline-evidence/` files and archives them as build artifacts. You can screenshot the Jenkins stage view, the console output from `Docker Evidence`, and the console output from `Kubernetes Evidence`.

If Jenkins runs inside a Docker agent, the pipeline checks backend health from inside the Compose network instead of using `localhost`. This avoids screenshots failing because published Docker ports belong to the Docker host rather than the Jenkins container.

## 3. Kubernetes Running Screenshot

To capture Kubernetes from Jenkins, run the pipeline with:

```text
DEPLOY_TO_K8S=true
```

If you are deploying to EKS and Jenkins needs to configure kubeconfig, also set:

```text
UPDATE_EKS_KUBECONFIG=true
```

For a small demo cluster, keep:

```text
K8S_REPLICA_COUNT=1
```

This keeps the screenshot run lightweight and avoids rollouts getting stuck because the cluster cannot schedule multiple replicas.

Screenshot the `Kubernetes Evidence` stage console output. It prints:

```bash
kubectl -n dockerized-microservices get pods -o wide
kubectl -n dockerized-microservices get svc -o wide
kubectl -n dockerized-microservices get ingress -o wide
```

The same output is archived in:

```text
pipeline-evidence/kubernetes-pods.txt
pipeline-evidence/kubernetes-services.txt
pipeline-evidence/kubernetes-ingress.txt
pipeline-evidence/kubernetes-events.txt
pipeline-evidence/backend-deployment-describe.txt
pipeline-evidence/frontend-deployment-describe.txt
```

Save as:

```text
screenshots/kubernetes-running.png
```

## 4. Docker Image Screenshot

To capture Docker evidence from Jenkins, screenshot the `Docker Evidence` stage console output. It prints:

```bash
docker images
docker compose ps
docker ps --filter "name=dmd-"
```

The same output is archived in:

```text
pipeline-evidence/docker-images.txt
pipeline-evidence/docker-compose-ps.txt
pipeline-evidence/docker-running-containers.txt
```

### Docker Hub

Replace `<username>` with your Docker Hub username:

```bash
docker login
docker tag dockerized-microservices-backend:latest <username>/dockerized-microservices-backend:v1
docker tag dockerized-microservices-frontend:latest <username>/dockerized-microservices-frontend:v1
docker push <username>/dockerized-microservices-backend:v1
docker push <username>/dockerized-microservices-frontend:v1
```

Open Docker Hub and screenshot the repository tag page.

Save as:

```text
screenshots/dockerhub-images.png
```

### AWS ECR

Replace the placeholders:

```bash
aws ecr create-repository --repository-name dockerized-microservices-backend --region us-east-1
aws ecr create-repository --repository-name dockerized-microservices-frontend --region us-east-1

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag dockerized-microservices-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/dockerized-microservices-backend:v1
docker tag dockerized-microservices-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/dockerized-microservices-frontend:v1

docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/dockerized-microservices-backend:v1
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/dockerized-microservices-frontend:v1
```

Open AWS Console -> ECR -> Repositories and screenshot the image tag list.

Save as:

```text
screenshots/ecr-images.png
```

## 5. README and GitHub Repo Screenshot

Push the project:

```bash
git init
git add .
git commit -m "Add Dockerized Microservices Deployment portfolio project"
git branch -M main
git remote add origin https://github.com/<your-username>/dockerized-microservices-deployment.git
git push -u origin main
```

Open the GitHub repository in your browser and capture:

- Folder structure
- Rendered README
- `backend/`, `frontend/`, `k8s/`, `helm/`, and `Jenkinsfile`

Save as:

```text
screenshots/github-repository.png
```

## Screenshot Tips

- On Windows, press `Win + Shift + S` to capture a selected area.
- Use Windows Terminal with a larger font for readable command screenshots.
- Crop screenshots to the important area only.
- Do not screenshot secrets, tokens, AWS account details, or passwords.
