import os
import datetime
import time
import logging 
import pytz
import pickle
import pandas as pd
import io
import psycopg
import joblib

from prefect import task, flow

from evidently.report import Report
from evidently import ColumnMapping
from evidently.metrics import ColumnDriftMetric, DatasetDriftMetric, DatasetMissingValuesMetric
from evidently.metrics import ColumnQuantileMetric, ColumnValueRangeMetric

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

SEND_TIMEOUT = 10

host = os.getenv("PGHOST")
user = os.getenv("PGUSER")
password = os.getenv("PGPASSWORD")
dbname = os.getenv("PGDATABASE")

create_table_statement = """
drop table if exists dummy_metrics;
create table dummy_metrics(
	timestamp timestamp,
	prediction_drift float,
	num_drifted_columns integer,
	share_missing_values float,
	median_return float,
	alpha_out_of_range_share float
)
"""

backfill = pd.read_parquet('backfill.parquet')
backfill['date'] = pd.to_datetime(backfill['date'])
month_ref_start = '2024-01-01'
month_ref_end = '2025-01-01'
reference_data = backfill.loc[(backfill['date']>month_ref_start) & (backfill['date']<month_ref_end)]
new_data = backfill.loc[backfill['date']>=month_ref_end]

ticker_list = backfill['ticker'].unique().tolist()
num_features = ['alpha', 'beta', 'month_index', 'index_avg', 'historical_vol', 
				'eom_10yr', '10yr_avg', 'spread', 'vix_avg']
cat_features = ['sector']

column_mapping = ColumnMapping(
    prediction='predicted_1m_return',
    numerical_features=num_features,
    categorical_features=cat_features,
    target='future_1m_return'
)

report = Report(metrics = [
    ColumnDriftMetric(column_name='predicted_1m_return'),
    DatasetDriftMetric(),
    DatasetMissingValuesMetric(),
    ColumnQuantileMetric(column_name='future_1m_return', quantile=0.5),
    ColumnValueRangeMetric(column_name='alpha', left=-0.0025, right=0.0025)
])

@task
def prep_db():
	with psycopg.connect(f"host={host} port=5432 dbname=postgres user={user} password={password}", autocommit=True) as conn:
		with conn.cursor() as cur:
			cur.execute("SELECT 1 FROM pg_database WHERE datname='test'")
			if cur.fetchone() is None:
				cur.execute("create database test;")
	with psycopg.connect(f"host={host} port=5432 dbname={dbname} user={user} password={password}") as conn:
		conn.execute(create_table_statement)

@task
def calculate_metrics_postgresql(curr, i):
	current_month = (pd.to_datetime(month_ref_end) + pd.DateOffset(months=i)).strftime('%Y-%m-%d')
	current_data = new_data[new_data['date']==current_month]

	#current_data.fillna(0, inplace=True)
	# current_data['prediction'] = results[results['ticker']==ticker_list[i]]['predicted_1m_return']

	report.run(reference_data = reference_data, current_data = current_data,
		column_mapping=column_mapping)

	result = report.as_dict()

	date = current_month
	prediction_drift = result['metrics'][0]['result']['drift_score']
	num_drifted_columns = result['metrics'][1]['result']['number_of_drifted_columns']
	share_missing_values = result['metrics'][2]['result']['current']['share_of_missing_values']
	median_return = result['metrics'][3]['result']['current']['value']
	alpha_out_of_range_share = result['metrics'][4]['result']['current']['share_not_in_range']

	curr.execute(
		"insert into dummy_metrics(timestamp, prediction_drift, num_drifted_columns, \
            share_missing_values, median_return, alpha_out_of_range_share) values (%s, %s, %s, %s, %s, %s)",
		(date, prediction_drift, num_drifted_columns, 
            share_missing_values, median_return, alpha_out_of_range_share)
	)

@flow
def batch_monitoring_backfill():
	prep_db()
	last_send = datetime.datetime.now() - datetime.timedelta(seconds=10)
	total_month = pd.Period('2025-07-01', freq='M') - pd.Period(month_ref_end, freq='M')
	with psycopg.connect(f"host={host} port=5432 dbname={dbname} user={user} password={password}", autocommit=True) as conn:
		for i in range(total_month.n):
			with conn.cursor() as curr:
				calculate_metrics_postgresql(curr, i)

			new_send = datetime.datetime.now()
			seconds_elapsed = (new_send - last_send).total_seconds()
			if seconds_elapsed < SEND_TIMEOUT:
				time.sleep(SEND_TIMEOUT - seconds_elapsed)
			while last_send < new_send:
				last_send = last_send + datetime.timedelta(seconds=10)
			logging.info("data sent")

if __name__ == '__main__':
	batch_monitoring_backfill()