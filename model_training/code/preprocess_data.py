import os
import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction import DictVectorizer


def dump_pickle(obj, filename: str):
    with open(filename, "wb") as f_out:
        return pickle.dump(obj, f_out)


def read_dataframe(filename: str):
    df = pd.read_parquet(filename)
    # check nan rows
    nan_rows = df[df.isnull().any(axis=1)]
    # print(nan_rows)
    return df


def preprocess(df: pd.DataFrame, dv: DictVectorizer, fit_dv: bool = False):
    categorical = ['sector']
    numerical = ['month_index', 'index_avg', 'alpha', 'beta', 'historical_vol', 'eom_10yr',
                 '10yr_avg', 'spread', 'vix_avg']
    dicts = df[categorical + numerical].to_dict(orient='records')
    if fit_dv:
        X = dv.fit_transform(dicts)
    else:
        X = dv.transform(dicts)
    return X, dv


def run_data_prep(raw_data_path: str, dest_path: str):
    # Load parquet files
    df = read_dataframe(
        os.path.join(raw_data_path, "features.parquet")
    )
    
    train_pct = 0.7
    val_pct = train_pct + 0.15
    unique_dates = df['date'].drop_duplicates().sort_values()
    n_dates = len(unique_dates)
    train_dates = unique_dates[:int(n_dates*train_pct)]
    val_dates = unique_dates[int(n_dates*train_pct): int(n_dates*val_pct)]
    test_dates = unique_dates[int(n_dates*val_pct):]
    df_train = df[df['date'].isin(train_dates)]
    df_val = df[df['date'].isin(val_dates)]
    df_test = df[df['date'].isin(test_dates)]
    
    # Extract the target
    target = 'future_1m_return'
    y_train = df_train[target].values
    y_val = df_val[target].values
    y_test = df_test[target].values

    # Fit the DictVectorizer and preprocess data
    dv = DictVectorizer()
    X_train, dv = preprocess(df_train, dv, fit_dv=True)
    X_val, _ = preprocess(df_val, dv, fit_dv=False)
    X_test, _ = preprocess(df_test, dv, fit_dv=False)
    
    # Create dest_path folder unless it already exists
    os.makedirs(dest_path, exist_ok=True)

    # Save DictVectorizer and datasets
    dump_pickle(dv, os.path.join(dest_path, "dv.pkl"))
    dump_pickle((X_train, y_train), os.path.join(dest_path, "train.pkl"))
    dump_pickle((X_val, y_val), os.path.join(dest_path, "val.pkl"))
    dump_pickle((X_test, y_test), os.path.join(dest_path, "test.pkl"))


if __name__ == '__main__':
    run_data_prep(raw_data_path='../files/', dest_path='../files/output/')