pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_REPO = 'techiehrishi0727/authvote'
        DOCKER_HUB_URL = 'https://index.docker.io/v1/'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker image') {
            steps {
                sh 'docker build --tag "$IMAGE_REPO:$BUILD_NUMBER" --tag "$IMAGE_REPO:latest" .'
            }
        }

        stage('Verify container health over HTTP') {
            steps {
                script {
                    def safeJobName = env.JOB_NAME.replaceAll(/[^A-Za-z0-9_.-]/, '-')
                    def temporaryContainer = "authvote-ci-${safeJobName}-${env.BUILD_NUMBER}"

                    withEnv([
                        "CI_CONTAINER_NAME=${temporaryContainer}",
                        "CI_IMAGE=${env.IMAGE_REPO}:${env.BUILD_NUMBER}"
                    ]) {
                        try {
                            sh '''#!/bin/sh
                                set -eu

                                docker run --detach --name "$CI_CONTAINER_NAME" --publish 127.0.0.1::8000 "$CI_IMAGE" >/dev/null

                                port_mapping=$(docker port "$CI_CONTAINER_NAME" 8000/tcp)
                                host_port=${port_mapping##*:}
                                case "$host_port" in
                                    ''|*[!0-9]*)
                                        echo "Could not determine the temporary container's host port."
                                        exit 1
                                        ;;
                                esac

                                attempt=0
                                while [ "$attempt" -lt 30 ]; do
                                    status=$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 2 "http://127.0.0.1:${host_port}/" 2>/dev/null || true)
                                    if [ "$status" = "200" ]; then
                                        echo "HTTP check passed: GET / returned 200."
                                        exit 0
                                    fi

                                    attempt=$((attempt + 1))
                                    sleep 1
                                done

                                echo "HTTP check failed; container logs follow:"
                                docker logs "$CI_CONTAINER_NAME" || true
                                exit 1
                            '''
                        } finally {
                            sh 'docker rm --force "$CI_CONTAINER_NAME" >/dev/null 2>&1 || true'
                        }
                    }
                }
            }
        }

        stage('Docker Hub login') {
            steps {
                script {
                    docker.withRegistry(env.DOCKER_HUB_URL, 'dockerhub-creds') {
                        sh 'docker image inspect "$IMAGE_REPO:$BUILD_NUMBER" >/dev/null'
                        echo 'Docker Hub credential scope is ready for the push stage.'
                    }
                }
            }
        }

        stage('Push images to Docker Hub') {
            steps {
                script {
                    docker.withRegistry(env.DOCKER_HUB_URL, 'dockerhub-creds') {
                        docker.image("${env.IMAGE_REPO}:${env.BUILD_NUMBER}").push()
                        docker.image("${env.IMAGE_REPO}:latest").push()
                    }
                }
            }
        }

        
        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'k8s-deployer-token',
                        variable: 'K8S_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu

                        KCFG=$(mktemp)
                        trap 'rm -f "$KCFG"' EXIT

                        kubectl --kubeconfig="$KCFG" config set-cluster minikube \
                            --server=https://192.168.49.2:8443 \
                            --certificate-authority=/var/lib/jenkins/k8s-ca.crt \
                            --embed-certs=true

                        kubectl --kubeconfig="$KCFG" config set-credentials jenkins-deployer \
                            --token="$K8S_TOKEN"

                        kubectl --kubeconfig="$KCFG" config set-context deploy \
                            --cluster=minikube \
                            --user=jenkins-deployer \
                            --namespace=default

                        kubectl --kubeconfig="$KCFG" config use-context deploy

                        kubectl --kubeconfig="$KCFG" set image deployment/authvote \
                            authvote="$IMAGE_REPO:$BUILD_NUMBER"

                        kubectl --kubeconfig="$KCFG" rollout status deployment/authvote \
                            --timeout=180s

                        kubectl --kubeconfig="$KCFG" get deployment authvote
                    '''
                }
            }
        }

    }
}
