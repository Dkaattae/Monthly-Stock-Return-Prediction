import os
import pickle
import mlflow
import numpy as np
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from hyperopt.pyll import scope
import xgboost as xgb
from sklearn.metrics import root_mean_squared_error

def set_mlflow_tracking_uri():
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLFlow tracking URI set to: {tracking_uri}")

def load_pickle(filename: str):
    with open(filename, "rb") as f_in:
        return pickle.load(f_in)


def run_optimization(data_path: str, num_trials: int):
    set_mlflow_tracking_uri()
    mlflow.set_experiment("stock-return-prediction-hyperopt")

    X_train, y_train = load_pickle(os.path.join(data_path, "train.pkl"))
    X_val, y_val = load_pickle(os.path.join(data_path, "val.pkl"))

    
    search_space = {
        'max_depth': scope.int(hp.quniform('max_depth', 5, 100, 5)),
        'n_estimators': scope.int(hp.quniform('n_estimators', 50, 300, 50)),
        'learning_rate': hp.loguniform('learning_rate', -7, 0),
        'reg_alpha': hp.loguniform('reg_alpha', -5, -1),
        'reg_lambda': hp.loguniform('reg_lambda', -6, -1),
        'min_child_weight': hp.loguniform('min_child_weight', -1, 3),
        'objective': 'reg:squarederror',
        'random_state': 42
    }

    def objective(params):
        with mlflow.start_run():
            mlflow.set_tag("model", "xgboost")
            mlflow.log_params(params)
            xgb_model = xgb.XGBRegressor(**params)
            xgb_model.fit(X_train, y_train)
            y_pred = xgb_model.predict(X_val)
            rmse = root_mean_squared_error(y_val, y_pred)
            mlflow.log_metric("rmse", rmse)

        return {'loss': rmse, 'status': STATUS_OK}

    rstate = np.random.default_rng(42)  # for reproducible results
    best_result = fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=num_trials,
        trials=Trials(),
        rstate=rstate
    )
    return best_result

if __name__ == '__main__':
    run_optimization('../files/output', 15)