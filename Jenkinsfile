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
                    sh 'docker-compose -f docker-compose.yml build web'
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
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