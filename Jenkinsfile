pipeline {
    agent any

    environment {
        DOCKER_HUB_REPO          = "dataguru97/studybuddy"
        DOCKER_HUB_CREDENTIALS_ID = "dockerhub-token"
        GITHUB_REPO              = "https://github.com/data-guru0/STUDY-BUDDY-AI.git"
        IMAGE_TAG                = "v${BUILD_NUMBER}"
        ARGOCD_SERVER            = "34.45.193.5:31704"
        ARGOCD_APP               = "study"
        K8S_SERVER               = "https://192.168.49.2:8443"
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Checking out ${GITHUB_REPO} @ main"
                checkout scmGit(
                    branches: [[name: '*/main']],
                    extensions: [],
                    userRemoteConfigs: [[
                        credentialsId: 'github-token',
                        url: "${GITHUB_REPO}"
                    ]]
                )
            }
        }

        stage('Lint') {
            steps {
                sh '''
                pip install --quiet ruff
                ruff check . --select E,W,F --ignore E501
                echo "Lint passed."
                '''
            }
        }

        stage('Build Docker image') {
            steps {
                script {
                    echo "Building image ${DOCKER_HUB_REPO}:${IMAGE_TAG}"
                    dockerImage = docker.build("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                }
            }
        }

        stage('Security scan') {
            steps {
                sh '''
                docker run --rm \
                    -v /var/run/docker.sock:/var/run/docker.sock \
                    aquasec/trivy:latest image \
                    --exit-code 0 \
                    --severity HIGH,CRITICAL \
                    --no-progress \
                    ${DOCKER_HUB_REPO}:${IMAGE_TAG}
                echo "Security scan complete."
                '''
            }
        }

        stage('Push to DockerHub') {
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', "${DOCKER_HUB_CREDENTIALS_ID}") {
                        dockerImage.push("${IMAGE_TAG}")
                        dockerImage.push("latest")
                    }
                }
            }
        }

        stage('Update deployment manifest') {
            steps {
                sh """
                sed -i 's|image: ${DOCKER_HUB_REPO}:.*|image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}|' manifests/deployment.yaml
                echo "Deployment manifest updated to ${IMAGE_TAG}"
                """
            }
        }

        stage('Commit & push manifest') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-token',
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_PASS'
                )]) {
                    sh '''
                    git config user.name  "ci-bot"
                    git config user.email "ci@studybuddy.ai"
                    git add manifests/deployment.yaml
                    git diff --staged --quiet && echo "No manifest change" || \
                        git commit -m "ci: update image tag to ${IMAGE_TAG} [skip ci]"
                    git push https://${GIT_USER}:${GIT_PASS}@github.com/data-guru0/STUDY-BUDDY-AI.git HEAD:main
                    '''
                }
            }
        }

        stage('Install CLI tools') {
            steps {
                sh '''
                echo "Installing kubectl and argocd CLI..."
                curl -sSLO "https://dl.k8s.io/release/$(curl -sSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                chmod +x kubectl && mv kubectl /usr/local/bin/kubectl

                curl -sSL -o /usr/local/bin/argocd \
                    https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
                chmod +x /usr/local/bin/argocd
                echo "CLI tools installed."
                '''
            }
        }

        stage('Sync ArgoCD') {
            steps {
                kubeconfig(credentialsId: 'kubeconfig', serverUrl: "${K8S_SERVER}") {
                    sh '''
                    ARGOCD_PWD=$(kubectl get secret -n argocd argocd-initial-admin-secret \
                        -o jsonpath="{.data.password}" | base64 -d)
                    argocd login ${ARGOCD_SERVER} --username admin --password "$ARGOCD_PWD" --insecure
                    argocd app sync ${ARGOCD_APP} --force
                    argocd app wait ${ARGOCD_APP} --health --timeout 120
                    echo "ArgoCD sync complete."
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded — ${DOCKER_HUB_REPO}:${IMAGE_TAG} is live."
        }
        failure {
            echo "Pipeline failed at stage. Check console output above."
        }
        always {
            cleanWs()
        }
    }
}
