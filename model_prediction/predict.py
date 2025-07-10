import os
import json
import pickle
import requests
import pandas as pd
import mlflow

def is_mlflow_server_alive():
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "")
    try:
        response = requests.get(tracking_uri)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_model_location(run_id, model_name='model'):
    model_location = os.getenv('MODEL_LOCATION')

    if model_location is not None:
        return model_location
    
    s3_bucket = os.getenv('S3_BUCKET', 'mlflow-artifacts-2025mlops')
    s3_prefix = os.getenv('S3_PREFIX', 'mlflow')
    experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID', '2')
    s3_uri = f's3://{s3_bucket}/{s3_prefix}/{experiment_id}/{run_id}/artifacts/{model_name}'
    return s3_uri

def get_run_id_from_registry(model_name='model', model_stage='Production'):
    client = mlflow.tracking.MlflowClient()
    versions = client.get_latest_versions(model_name, stages=[model_stage])
    if not versions:
        raise Exception("No model found in the specified stage.")
    return versions[0].run_id

def load_model_from_registry(model_name, artifact_name):
    mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    model = mlflow.pyfunc.load_model(f'models:/{model_name}/Production')
    registry_run_id = get_run_id_from_registry()
    artifact = mlflow.artifacts.download_artifacts(run_id=registry_run_id, artifact_path=artifact_name)
        
    print('load model and artifact from MLflow server')
    return (model, artifact, registry_run_id)

def load_model_from_s3(run_id, artifact_name):
    model_location = get_model_location(run_id)
    model = mlflow.pyfunc.load_model(model_location)
    artifact_uri = model_location.rsplit('/', 1)[0] + '/' + artifact_name
    artifact_path = mlflow.artifacts.download_artifacts(artifact_uri=artifact_uri)
    print('load model from S3')
    return (model, artifact_path, run_id)

def load_model_from_local(model_example_path, artifact_name):
    model = mlflow.pyfunc.load_model(model_example_path)
    artifacts = model_example_path.rsplit('/',1)[0] + '/' + artifact_name
    run_id = 'test'
    print('load model from test examples')
    return (model, artifacts, run_id)

def load_model_artifact(model_name='model', 
                        artifact_name='dv.pkl', 
                        model_example_path='./artifacts/model'):
    if is_mlflow_server_alive():
        try:
            return load_model_from_registry(model_name, artifact_name)
        except Exception:
            print("Mlflow server not accessible. try to load model from S3 bucket")

    run_id = os.getenv('MLFLOW_RUN_ID')
    if run_id:
        try: 
            return load_model_from_s3(run_id, artifact_name)
        except Exception:
            print('S3 not accessible or model not founnd')
            try:
                return load_model_from_local(model_example_path)
            except Exception:
                print('failed to load model')
    else:
        print('run_id not found')
    return load_model_from_local(model_example_path, artifact_name)

def load_artifact(artifact_path):
    with open(artifact_path, 'rb') as f:
        dv = pickle.load(f)
    return dv

def prepare_features(new_data, dv):
    categorical = ['sector']
    numerical = ['month_index', 'index_avg', 'alpha', 'beta', 'historical_vol', 'eom_10yr',
                 '10yr_avg', 'spread', 'vix_avg']
    dicts = new_data[categorical + numerical].to_dict(orient='records')
    X = dv.transform(dicts)
    return X

def predict(new_data):
    model, artifact_path, run_id = load_model_artifact()
    dv = load_artifact(artifact_path)
    X = prepare_features(new_data, dv)
    prediction = model.predict(X)
    new_data['predicted_1m_return'] = prediction
    new_data['model_version'] = run_id
    new_data["date"] = pd.to_datetime(new_data["date"], errors="coerce", unit="ms")
    new_data["date"] = new_data["date"].dt.strftime("%Y-%m-%d")
    return new_data

if __name__ == "__main__":
    new_data = pd.read_json('json_records.json')
    prediction = predict(new_data)
    print(prediction)