import os
import pickle
import mlflow

from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient
import xgboost as xgb
from sklearn.metrics import root_mean_squared_error

HPO_EXPERIMENT_NAME = "stock-return-prediction-hyperopt"
EXPERIMENT_NAME = "xgboost-best-models"
XGBOOST_PARAMS = ['max_depth', 'n_estimators', 'learning_rate', 
                  'reg_alpha', 'reg_lambda', 'min_child_weight',
                  'objective', 'random_state']


def set_mlflow_tracking_uri():
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLFlow tracking URI set to: {tracking_uri}")

def load_pickle(filename):
    with open(filename, "rb") as f_in:
        return pickle.load(f_in)


def train_and_log_model(data_path, params):
    set_mlflow_tracking_uri()
    mlflow.set_experiment(EXPERIMENT_NAME)
    X_train, y_train = load_pickle(os.path.join(data_path, "train.pkl"))
    X_val, y_val = load_pickle(os.path.join(data_path, "val.pkl"))
    X_test, y_test = load_pickle(os.path.join(data_path, "test.pkl"))

    with mlflow.start_run():
        mlflow.autolog(disable=True)
        new_params = {}
        for param in XGBOOST_PARAMS:
            if param == 'objective':
                new_params[param] = params[param]
            if param in ['learning_rate', 'reg_alpha', 'reg_lambda', 'min_child_weight']:
                new_params[param] = float(params[param])
            if param in ['max_depth', 'n_estimators', 'random_state']:
                new_params[param] = int(params[param])
        # print(new_params)
        xgb_model = xgb.XGBRegressor(**new_params)
        xgb_model.fit(X_train, y_train)
        mlflow.set_tag("model", "xgboost")
        mlflow.log_params(new_params)

        # Evaluate model on the validation and test sets
        val_rmse = root_mean_squared_error(y_val, xgb_model.predict(X_val))
        mlflow.log_metric("val_rmse", val_rmse)
        test_rmse = root_mean_squared_error(y_test, xgb_model.predict(X_test))
        mlflow.log_metric("test_rmse", test_rmse)
        mlflow.xgboost.log_model(xgb_model, artifact_path="model")
        mlflow.log_artifact(os.path.join(data_path, "dv.pkl"))

def run_register_model(data_path: str, top_n: int):

    client = MlflowClient()

    # Retrieve the top_n model runs and log the models
    experiment = client.get_experiment_by_name(HPO_EXPERIMENT_NAME)
    runs = client.search_runs(
        experiment_ids=experiment.experiment_id,
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=top_n,
        order_by=["metrics.rmse ASC"]
    )
    
    for run in runs:
        train_and_log_model(data_path=data_path, params=run.data.params)

    # Select the model with the lowest test RMSE
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    best_run = client.search_runs(
        experiment_ids=experiment.experiment_id,
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=top_n,
        order_by=["metrics.test_rmse ASC"])[0]

    # Register the best model
    run_id = best_run.info.run_id
    model_uri = f'runs:/{run_id}/model'
    mlflow.register_model(model_uri=model_uri, name=EXPERIMENT_NAME)


if __name__ == '__main__':
    run_register_model('../files/output', 2)