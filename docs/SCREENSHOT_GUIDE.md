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
   - Push Images
   - Deploy

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

## 3. Kubernetes Running Screenshot

Build images:

```bash
docker compose build
```

For minikube:

```bash
minikube start
minikube image load dockerized-microservices-backend:latest
minikube image load dockerized-microservices-frontend:latest
```

Deploy:

```bash
kubectl apply -f k8s/
```

Capture these terminal commands:

```bash
kubectl -n dockerized-microservices get pods -o wide
kubectl -n dockerized-microservices get svc
kubectl -n dockerized-microservices get ingress
```

Save as:

```text
screenshots/kubernetes-running.png
```

Clean up when finished:

```bash
kubectl delete -f k8s/
```

## 4. Docker Image Screenshot

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
