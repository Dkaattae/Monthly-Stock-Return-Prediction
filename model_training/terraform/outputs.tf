output "mlflow_server_public_ip" {
  description = "Public IP address of the MLflow server"
  value       = aws_instance.mlflow_server.public_ip
}

output "mlflow_server_public_dns" {
  description = "Public DNS name of the MLflow server"
  value       = aws_instance.mlflow_server.public_dns
}

output "mlflow_url" {
  description = "MLflow tracking server URL"
  value       = "http://${aws_instance.mlflow_server.public_dns}:5000"
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for MLflow artifacts"
  value       = aws_s3_bucket.mlflow_artifacts.bucket
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.mlflow_db.endpoint
}

output "ssh_connection_command" {
  description = "SSH command to connect to the MLflow server"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ec2-user@${aws_instance.mlflow_server.public_dns}"
}