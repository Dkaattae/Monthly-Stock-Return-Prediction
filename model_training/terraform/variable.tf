variable "aws_region" {
  default = "us-east-1"
}

variable "db_password" {
  description = "Password for the RDS Postgres instance"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "mlflow-prod"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access MLflow server"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this in production
}

variable "key_pair_name" {
  description = "Name of the AWS key pair for EC2 access"
  type        = string
}