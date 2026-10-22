# AuthVote: CI/CD with Jenkins, Docker, and Kubernetes

AuthVote is a student authentication and digital voting project. This repository demonstrates a CI/CD workflow in which a source-code change is built into a Docker image, checked over HTTP, published to Docker Hub, and deployed to Kubernetes using Jenkins and Minikube.

**Repository:** [techie-hrushik027/AuthVote](https://github.com/techie-hrushik027/AuthVote)

## 1. Project Overview

AuthVote is a prototype student-election application. Its intended workflow includes student authentication, election instructions, rapid-fire questions, candidate selection, and vote submission.

The project demonstrates two concepts:

1. A student authentication and digital voting application.
2. A repeatable CI/CD pipeline for building and deploying an existing application.

## 2. Technologies Used

| Area | Technology |
| --- | --- |
| Source control | Git and GitHub |
| CI/CD | Jenkins |
| Application backend | Python and FastAPI |
| Frontend | HTML, CSS, and JavaScript |
| Database | MySQL |
| Containerization | Docker |
| Image registry | Docker Hub |
| Orchestration | Kubernetes and Minikube |
| Cloud environment | AWS EC2 running Ubuntu |

## 3. CI/CD Architecture

The project follows this delivery flow:

```text
Developer changes source code
          |
          v
Push commit to GitHub
          |
          v
Jenkins checks out the revision
          |
          v
Docker builds the application image
with a build-number tag and latest
          |
          v
Jenkins runs a temporary container
and checks GET / for HTTP 200
          |
          v
Jenkins pushes both image tags
to Docker Hub
          |
          v
Jenkins updates the authvote
Kubernetes Deployment
          |
          v
Minikube completes the rollout
and serves the application
```

## 4. Jenkins Pipeline Stages

The root `Jenkinsfile` defines these stages:

| Stage | Purpose |
| --- | --- |
| Checkout | Retrieves the configured source-code revision. |
| Build Docker image | Builds the application image with a build-number tag and the `latest` tag. |
| Verify container health over HTTP | Starts a temporary container and retries the root endpoint until it returns HTTP 200 or the check times out. |
| Docker Hub login | Uses Jenkins credential ID `dockerhub-creds` for registry authentication. |
| Push images to Docker Hub | Publishes the build-number image and the `latest` tag. |
| Deploy to Kubernetes | Uses credential ID `k8s-deployer-token`, updates the `authvote` Deployment, and waits for its rollout. |

The image repository is `techiehrishi0727/authvote`. For example, build number `11` produces the `11` and `latest` tags.

The HTTP smoke check confirms that the root page responds successfully. It does not test all authentication, database, or voting workflows, and it is not a substitute for comprehensive unit, integration, or security testing.

## 5. Repository Structure

```text
AuthVote/
|-- Admin_Console/
|   `-- main.cpp
|-- Backend/
|   |-- app.py
|   `-- admin_tools.py
|-- Database/
|   `-- Authvote_schema.sql
|-- Frontend/
|   |-- login.html
|   |-- instructions.html
|   |-- rapid_fire.html
|   |-- voting_ballot.html
|   `-- dashboard.html
|-- k8s/
|   `-- authvote.yaml
|-- .dockerignore
|-- .gitignore
|-- Dockerfile
|-- Jenkinsfile
|-- requirements.txt
`-- README.md
```

## 6. Deployment Configuration

The course demo environment uses an Ubuntu EC2 instance running Jenkins, Docker, `kubectl`, and Minikube. Configure a Jenkins pipeline job to use this repository and its root `Jenkinsfile`. The pipeline uses shell commands and requires Docker, `curl`, and `kubectl` on its agent.

The Jenkins credentials are:

- `dockerhub-creds` for Docker Hub authentication.
- `k8s-deployer-token` for a Kubernetes service-account token.

Store credentials in Jenkins Credentials. Do not commit registry passwords, Kubernetes tokens, or database passwords to GitHub.

The deployment stage currently uses the Kubernetes API endpoint `https://192.168.49.2:8443` and CA certificate `/var/lib/jenkins/k8s-ca.crt`. These values are specific to the current Minikube environment and may need updating if the cluster is recreated. A GitHub webhook or automatic trigger should only be described as configured after it has been verified; the Jenkins job can also be started manually.

## 7. Kubernetes Deployment and Verification

The `k8s/authvote.yaml` manifest defines an AuthVote Deployment and a NodePort Service. The application container listens on port `8000`, and the Service uses NodePort `30080`.

Inspect the Kubernetes resources and rollout with:

```bash
kubectl get pods,deployments,services
kubectl rollout status deployment/authvote
kubectl logs deployment/authvote
```

From the EC2 host, check the application endpoint with:

```bash
curl -i http://192.168.49.2:30080/
```

The expected HTTP status for a successful root-page response is `200`. The node IP must match the active Minikube environment. For browser access, the demo can use `kubectl port-forward` and an SSH tunnel rather than exposing the NodePort publicly.

## 8. Demonstrating a Source-Code Change

Make a visible change to the login page and show it moving through the pipeline:

1. Edit a heading in `Frontend/login.html`.
2. Commit and push the change to GitHub.
3. Start the `AuthVote-CI-CD` Jenkins job.
4. Show the checkout and Docker build stages.
5. Show the successful HTTP smoke check.
6. Show both image tags published to Docker Hub.
7. Show the Kubernetes Deployment rollout.
8. Refresh the running application and demonstrate the updated heading.

This demonstrates how a source-code change becomes a container image and is rolled out to the application.

## 9. Validation and Limitations

The current pipeline builds a Docker image, performs an HTTP smoke check, publishes the image, and verifies the Kubernetes rollout. These steps do not establish that every authentication, database, or voting workflow works correctly.

The backend requires a reachable MySQL database and the `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` environment variables for database-backed functionality. Confirm the database configuration and connectivity before demonstrating sign-in or vote submission. Document any separately managed database accurately; the AuthVote Kubernetes manifest describes the application Deployment and Service.

Support a successful deployment claim with evidence from the actual environment, including the Jenkins build, Docker Hub image, Kubernetes resources, and running application.

## 10. Submission Evidence

Capture screenshots showing:

- The GitHub repository and its `Dockerfile`, `Jenkinsfile`, README, and Kubernetes manifest.
- A successful Jenkins pipeline with all stages completed.
- The corresponding build-number image in Docker Hub.
- Kubernetes pods, Deployment, and Service.
- The running AuthVote application.
- A visible source-code change in the deployed application after the pipeline completes.

A continuous demonstration video can show these steps in order, with a brief explanation of the CI/CD architecture and deployment process.
