aws_region = "us-east-1"
db_password = "your-secure-database-password-here"
environment = "mlflow-prod"
instance_type = "t3.medium"
db_instance_class = "db.t3.micro"
key_pair_name = "your-ec2-key-pair-name"

# Restrict access to your IP for security
allowed_cidr_blocks = ["YOUR_IP_ADDRESS/32"]