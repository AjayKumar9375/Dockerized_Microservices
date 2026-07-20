# Screenshot Guide

Use real output from Jenkins, Docker, Kubernetes, and your registry account. Keep screenshots cropped and readable.

## Architecture

Open `docs/architecture.mmd` in GitHub preview or https://mermaid.live and export the diagram.

Save as:

```text
screenshots/architecture-diagram.png
```

## Jenkins

Create a Jenkins Pipeline job that points to this repository and uses the root `Jenkinsfile`.

Capture the stage view after a successful run:

```text
Checkout -> Validate -> Build Images -> Test -> SonarQube -> Docker Evidence -> Push Images -> Deploy to Kubernetes -> Kubernetes Evidence
```

Save as:

```text
screenshots/jenkins-pipeline.png
```

## Docker Evidence

Run the pipeline with the default parameters. Screenshot the `Docker Evidence` console output.

The stage writes:

```text
pipeline-evidence/docker-images.txt
pipeline-evidence/docker-compose-ps.txt
pipeline-evidence/docker-containers.txt
pipeline-evidence/backend-health.json
```

Save the screenshot as:

```text
screenshots/docker-evidence.png
```

## Kubernetes Evidence

Run the pipeline with:

```text
DEPLOY_TO_K8S=true
K8S_REPLICAS=1
```

For EKS, also set:

```text
UPDATE_EKS_KUBECONFIG=true
AWS_REGION=<region>
EKS_CLUSTER_NAME=<cluster-name>
```

Screenshot the `Kubernetes Evidence` console output.

The stage writes:

```text
pipeline-evidence/kubernetes-pods.txt
pipeline-evidence/kubernetes-services.txt
pipeline-evidence/kubernetes-ingress.txt
pipeline-evidence/kubernetes-events.txt
pipeline-evidence/backend-logs.txt
```

Save the screenshot as:

```text
screenshots/kubernetes-evidence.png
```

## Registry

Run the pipeline with:

```text
PUSH_IMAGES=true
REGISTRY_TYPE=dockerhub
REGISTRY_NAMESPACE=<dockerhub-user>
```

For ECR, use:

```text
PUSH_IMAGES=true
REGISTRY_TYPE=ecr
AWS_ACCOUNT_ID=<account-id>
AWS_REGION=<region>
```

Open Docker Hub or AWS ECR and capture the pushed image tags.

Save as:

```text
screenshots/registry-images.png
```

## GitHub

Push the repository, then capture the GitHub page showing:

- `backend/`
- `frontend/`
- `k8s/`
- `helm/`
- `Jenkinsfile`
- rendered `README.md`

Save as:

```text
screenshots/github-repo.png
```
