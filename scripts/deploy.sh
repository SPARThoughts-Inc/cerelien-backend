#!/usr/bin/env bash
set -euo pipefail

echo "=== Cerelien Backend Deployment ==="

AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO="cerelien-api"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "1. Running tests..."
poetry run pytest --cov=app --cov-fail-under=80 -q

echo "2. Building Docker image..."
docker build -t ${ECR_REPO}:${IMAGE_TAG} .

echo "3. Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

echo "4. Tagging and pushing image..."
docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}
docker push ${ECR_URI}:${IMAGE_TAG}

echo "5. Deploying CDK stack..."
cd cdk
npm ci
npx cdk deploy --require-approval never

echo "6. Updating ECS service..."
aws ecs update-service \
  --cluster cerelien-cluster \
  --service cerelien-api \
  --force-new-deployment \
  --region ${AWS_REGION}

echo "=== Deployment complete ==="
echo "ALB DNS: $(aws cloudformation describe-stacks --stack-name CerelienBackendStack --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' --output text)"
