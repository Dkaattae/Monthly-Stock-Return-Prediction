from datetime import date
from prefect import flow, task
from get_stock_price import download_data
from transform_stock_price import transform_data
from preprocess_data import run_data_prep
from hpo import run_optimization
from register_model import run_register_model

@task(retries=3, retry_delay_seconds=2)
def download_task(data_span=3, ticker_file_path='../files/spx_tickers.csv'):
    '''
    download data from internet
    '''
    download_data(data_span=data_span, ticker_file_path=ticker_file_path)

@task
def transform_task(last_date=date.today(), output_file_path='../files/features.parquet'):
    '''
    transform raw data into machine learning ready format
    '''
    features_df = transform_data(last_date)
    features_df.to_parquet(output_file_path, engine='pyarrow')

@task
def preprocess_task(raw_data_path='../files/', dest_path='../files/output/') -> None:
    '''
    dump four pickle files into output folder 
    dictVectorizer from training, X_train, X_val, X_test
    '''
    run_data_prep(raw_data_path, dest_path)

@task()
def hyperopt_task(dest_path='../files/output/', num_trials=15):
    '''
    start mlflow server, searching best pamameters based on val rmse, logging in mlflow
    '''
    # add data_path to experiment_tracking/output instead of default ./output
    run_optimization(dest_path, num_trials)

@task()
def register_task(dest_path='../files/output/', top_n=2):
    '''
    find top models from hyperopt, run model on test dataset, logging in mlflow, 
    register the best on test set.
    '''
    run_register_model(dest_path, top_n)

@flow()
def main_flow(ticker_file_path, output_file_path, dest_path):
    """
    The main training pipeline
    ticker_file_path is the path where ticker files stored
    output_file_path is the path where transformed data stored, it should be in parquet format
    dest_path is where X_train, X_val and X_test stored
    """
    download_task(ticker_file_path=ticker_file_path)
    transform_task(output_file_path=output_file_path)
    raw_data_path = output_file_path.rsplit('/', 1)[0]
    preprocess_task(raw_data_path, dest_path)
    hyperopt_task(dest_path)
    register_task(dest_path)



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker_file_path", default='../files/spx_tickers.csv')
    parser.add_argument("--output_file_path", default='../files/features.parquet')
    parser.add_argument("--dest_path", default='../files/output/')
    args = parser.parse_args()
    main_flow(args.ticker_file_path, args.output_file_path, args.dest_path)