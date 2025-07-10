#!/bin/bash

# MLflow Installation and Setup Script
# This script is run automatically by EC2 user data

# Update system
sudo yum update -y

# Install Python 3.9 and pip
sudo yum install -y python3 python3-pip

# Install PostgreSQL client
sudo yum install -y postgresql

# Install MLflow and dependencies
sudo pip3 install mlflow psycopg2-binary boto3

# Create MLflow directory
sudo mkdir -p /opt/mlflow
sudo chown ec2-user:ec2-user /opt/mlflow

# Create MLflow configuration
cat > /opt/mlflow/mlflow.conf << EOF
DB_HOST=${db_host}
DB_USER=${db_user}
DB_PASSWORD=${db_password}
DB_NAME=${db_name}
S3_BUCKET=${s3_bucket}
AWS_REGION=${aws_region}
EOF

# Create systemd service file for MLflow
sudo tee /etc/systemd/system/mlflow.service > /dev/null << EOF
[Unit]
Description=MLflow Tracking Server
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/mlflow
Environment=AWS_DEFAULT_REGION=${aws_region}
ExecStart=/usr/local/bin/mlflow server \\
    --backend-store-uri postgresql://${db_user}:${db_password}@${db_host}:5432/${db_name} \\
    --default-artifact-root s3://${s3_bucket}/mlflow-artifacts \\
    --host 0.0.0.0 \\
    --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Wait for RDS to be ready
echo "Waiting for RDS to be ready..."
until pg_isready -h ${db_host} -p 5432 -U ${db_user}; do
    echo "RDS not ready yet, waiting 30 seconds..."
    sleep 30
done

# Create database and tables
PGPASSWORD=${db_password} psql -h ${db_host} -U ${db_user} -d ${db_name} -c "SELECT 1;" || {
    echo "Database connection failed"
    exit 1
}

# Initialize MLflow database
cd /opt/mlflow
mlflow db upgrade postgresql://${db_user}:${db_password}@${db_host}:5432/${db_name}

# Enable and start MLflow service
sudo systemctl daemon-reload
sudo systemctl enable mlflow
sudo systemctl start mlflow

# Create log directory and set up log rotation
sudo mkdir -p /var/log/mlflow
sudo chown ec2-user:ec2-user /var/log/mlflow

# Create a simple health check script
cat > /opt/mlflow/health_check.sh << EOF
#!/bin/bash
if curl -f -s http://localhost:5000/health > /dev/null; then
    echo "MLflow server is healthy"
    exit 0
else
    echo "MLflow server is not responding"
    exit 1
fi
EOF

chmod +x /opt/mlflow/health_check.sh

# Log completion
echo "MLflow installation completed at $(date)" >> /var/log/mlflow/install.log
echo "MLflow server should be accessible at http://$(curl -s http://169.254.169.254/latest/meta-data/public-hostname):5000" >> /var/log/mlflow/install.log