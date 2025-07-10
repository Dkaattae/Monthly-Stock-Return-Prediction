#!/bin/bash

# MLflow AWS Deployment Script
# This script automates the deployment of MLflow on AWS using Terraform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed. Please install Terraform first."
    exit 1
fi

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install and configure AWS CLI first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials are not configured. Please run 'aws configure' first."
    exit 1
fi

print_status "Starting MLflow deployment on AWS..."

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_warning "terraform.tfvars not found. Creating from example..."
    cp terraform.tfvars.example terraform.tfvars
    print_error "Please edit terraform.tfvars with your actual values before running this script again."
    exit 1
fi

# Initialize Terraform
print_status "Initializing Terraform..."
terraform init

# Validate Terraform configuration
print_status "Validating Terraform configuration..."
terraform validate

# Plan deployment
print_status "Planning deployment..."
terraform plan -out=tfplan

# Ask for confirmation
read -p "Do you want to apply this plan? (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled."
    exit 0
fi

# Apply deployment
print_status "Applying deployment..."
terraform apply tfplan

# Get outputs
print_status "Deployment completed! Here are the connection details:"
echo
echo "MLflow Server URL: $(terraform output -raw mlflow_url)"
echo "SSH Command: $(terraform output -raw ssh_connection_command)"
echo "S3 Bucket: $(terraform output -raw s3_bucket_name)"
echo

# Wait for MLflow to be ready
print_status "Waiting for MLflow server to be ready..."
MLFLOW_URL=$(terraform output -raw mlflow_url)
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -f -s "$MLFLOW_URL/health" > /dev/null 2>&1; then
        print_status "MLflow server is ready!"
        break
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS - MLflow not ready yet, waiting 30 seconds..."
    sleep 30
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    print_warning "MLflow server didn't respond after $MAX_ATTEMPTS attempts."
    print_warning "You can check the server status by SSH'ing into the instance and running:"
    print_warning "sudo systemctl status mlflow"
else
    print_status "MLflow is now accessible at: $MLFLOW_URL"
fi

# Clean up
rm -f tfplan

print_status "Deployment script completed!"
echo
echo "Next steps:"
echo "1. Access your MLflow server at: $MLFLOW_URL"
echo "2. Update your ML pipeline to use this tracking server"
echo "3. Set the following environment variables in your training environment:"
echo "   export MLFLOW_TRACKING_URI=$MLFLOW_URL"
echo "   export MLFLOW_S3_ENDPOINT_URL=https://s3.$(terraform output -raw aws_region).amazonaws.com"