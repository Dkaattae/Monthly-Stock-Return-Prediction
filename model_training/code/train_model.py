import os
import pickle

import xgboost as xgb
from sklearn.metrics import root_mean_squared_error

import mlflow
from mlflow.models.signature import infer_signature


def set_mlflow_tracking_uri():
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLFlow tracking URI set to: {tracking_uri}")

def load_pickle(filename: str):
    with open(filename, "rb") as f_in:
        return pickle.load(f_in)


def run_train(data_path: str):
    set_mlflow_tracking_uri()
    mlflow.set_experiment("stock-1month-return-prediction")
    X_train, y_train = load_pickle(os.path.join(data_path, "train.pkl"))
    X_val, y_val = load_pickle(os.path.join(data_path, "val.pkl"))
    
    with mlflow.start_run():

        mlflow.set_tag("developer", "KateChen")

        mlflow.log_param("train-data-path", "../files/features.parquet")
        mlflow.log_param("valid-data-path", "../files/features.parquet")

        n_estimators=100
        learning_rate=0.1
        max_depth=5

        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("learning_rate", learning_rate)
        mlflow.log_param("max_depth", max_depth)
        
        xgb_model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=n_estimators, 
                                     learning_rate=learning_rate, max_depth=max_depth)
        xgb_model.fit(X_train, y_train)
        y_pred = xgb_model.predict(X_val)
        rmse = root_mean_squared_error(y_val, y_pred)
        mlflow.log_metric("rmse", rmse)

        mlflow.log_artifact(local_path=os.path.join(data_path, "train.pkl"), artifact_path="models_pickle")

        input_example = X_train[:5].toarray()  
        signature = infer_signature(X_train.toarray(), xgb_model.predict(X_train))
        mlflow.sklearn.log_model(xgb_model, artifact_path="models_pickle", input_example=input_example, signature=signature)

        

if __name__ == '__main__':
    run_train('../files/output')