terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data source for latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# VPC and Networking
resource "aws_vpc" "mlflow_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.environment}-vpc"
  }
}

resource "aws_internet_gateway" "mlflow_igw" {
  vpc_id = aws_vpc.mlflow_vpc.id

  tags = {
    Name = "${var.environment}-igw"
  }
}

resource "aws_subnet" "mlflow_subnet_public" {
  vpc_id                  = aws_vpc.mlflow_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.environment}-public-subnet"
  }
}

resource "aws_subnet" "mlflow_subnet_private" {
  vpc_id            = aws_vpc.mlflow_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "${var.environment}-private-subnet"
  }
}

resource "aws_route_table" "mlflow_public_rt" {
  vpc_id = aws_vpc.mlflow_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.mlflow_igw.id
  }

  tags = {
    Name = "${var.environment}-public-rt"
  }
}

resource "aws_route_table_association" "mlflow_public_rta" {
  subnet_id      = aws_subnet.mlflow_subnet_public.id
  route_table_id = aws_route_table.mlflow_public_rt.id
}

# Security Groups
resource "aws_security_group" "mlflow_ec2_sg" {
  name        = "${var.environment}-ec2-sg"
  description = "Security group for MLflow EC2 instance"
  vpc_id      = aws_vpc.mlflow_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-ec2-sg"
  }
}

resource "aws_security_group" "mlflow_rds_sg" {
  name        = "${var.environment}-rds-sg"
  description = "Security group for MLflow RDS instance"
  vpc_id      = aws_vpc.mlflow_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.mlflow_ec2_sg.id]
  }

  tags = {
    Name = "${var.environment}-rds-sg"
  }
}

# S3 Bucket for MLflow artifacts
resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = "${var.environment}-mlflow-artifacts-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "${var.environment}-mlflow-artifacts"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 8
}

resource "aws_s3_bucket_versioning" "mlflow_artifacts_versioning" {
  bucket = aws_s3_bucket.mlflow_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mlflow_artifacts_encryption" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# IAM Role for EC2 instance
resource "aws_iam_role" "mlflow_ec2_role" {
  name = "${var.environment}-mlflow-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "mlflow_s3_policy" {
  name        = "${var.environment}-mlflow-s3-policy"
  description = "Policy for MLflow to access S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.mlflow_artifacts.arn,
          "${aws_s3_bucket.mlflow_artifacts.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "mlflow_ec2_s3_policy" {
  role       = aws_iam_role.mlflow_ec2_role.name
  policy_arn = aws_iam_policy.mlflow_s3_policy.arn
}

resource "aws_iam_instance_profile" "mlflow_ec2_profile" {
  name = "${var.environment}-mlflow-ec2-profile"
  role = aws_iam_role.mlflow_ec2_role.name
}

# RDS Subnet Group
resource "aws_db_subnet_group" "mlflow_db_subnet_group" {
  name       = "${var.environment}-db-subnet-group"
  subnet_ids = [aws_subnet.mlflow_subnet_public.id, aws_subnet.mlflow_subnet_private.id]

  tags = {
    Name = "${var.environment}-db-subnet-group"
  }
}

# RDS PostgreSQL Database
resource "aws_db_instance" "mlflow_db" {
  identifier = "${var.environment}-mlflow-db"
  
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = var.db_instance_class
  allocated_storage = 20
  storage_type      = "gp2"
  
  db_name  = "mlflow"
  username = "mlflow"
  password = var.db_password  # This is where you pass the db_password variable
  
  vpc_security_group_ids = [aws_security_group.mlflow_rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.mlflow_db_subnet_group.name
  
  skip_final_snapshot = true
  deletion_protection = false
  
  tags = {
    Name = "${var.environment}-mlflow-db"
  }
}

# User Data Script for EC2 Instance
locals {
  user_data = base64encode(templatefile("${path.module}/install_mlflow.sh", {
    db_host     = aws_db_instance.mlflow_db.endpoint
    db_user     = aws_db_instance.mlflow_db.username
    db_password = var.db_password
    db_name     = aws_db_instance.mlflow_db.db_name
    s3_bucket   = aws_s3_bucket.mlflow_artifacts.bucket
    aws_region  = var.aws_region
  }))
}

# EC2 Instance
resource "aws_instance" "mlflow_server" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  subnet_id              = aws_subnet.mlflow_subnet_public.id
  vpc_security_group_ids = [aws_security_group.mlflow_ec2_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.mlflow_ec2_profile.name
  
  user_data = local.user_data
  
  tags = {
    Name = "${var.environment}-mlflow-server"
  }
}