pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo 'Code checkout ho gaya!'
            }
        }

        stage('Build') {
            steps {
                script {
                    sh 'cp /var/jenkins_home/.env .env'
                    sh 'docker build -t tirgum-backend-pipeline-web -f backend/Dockerfile backend/'
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sh 'cp /var/jenkins_home/.env .env'
                    sh 'docker-compose -f docker-compose.yml up -d'
                }
            }
        }
    }

    post {
        success { echo 'Deploy successful!' }
        failure { echo 'Kuch toh gadbad hai!' }
    }
}