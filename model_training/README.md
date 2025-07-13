# model training

## environment setup
base image python 3.12   
`pip install -r requirements.txt`
`python training_flow.py`

environment variable MLFLOW_TRACKING_URI is exported, if mlflow server hosted in cloud   
if not, it will default to 'localhost:5000'

it will run tasks in flow:   
1, download data
2, transform data
3, preprocess data
4, hyperopt training
5, register model 

note: download data and transform data tasks are not robust in this pipeline.   
for data versioning, check my [data engineering project](https://github.com/Dkaattae/annual_quarter_report_and_stock_price)

# mlflow server
follow steps [here](https://github.com/DataTalksClub/mlops-zoomcamp/blob/main/02-experiment-tracking/mlflow_on_aws.md) to setup AWS

## terraform
use terraform to set up AWS services
S3 bucket, RDS postgres, EC2 instance,
and IAM role for EC2 to get access to S3
(not done)