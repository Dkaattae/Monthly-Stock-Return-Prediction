import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import date

import transform_stock_price

def get_month_index(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

def latest_calculation(stock_df, index_df, treasury_10y, treasury_2y, vix_df, end_date):
    capm_window_year = 1
    start_date = end_date.replace(year=end_date.year - capm_window_year)
    capm_window_mask = (stock_df['date'] > start_date) & (stock_df['date'] < end_date)
    capm_stock_df = stock_df.loc[capm_window_mask]
    capm_index_df = index_df.loc[capm_window_mask]
    end_date_results = transform_stock_price.cal_alpha_beta(capm_stock_df, capm_index_df, end_date)
        
    # get index average
    avg_start_date = end_date  - relativedelta(months=1)
    avg_window_mask = (index_df['date'] >= avg_start_date) & (index_df['date'] < end_date)
    end_date_index_avg = transform_stock_price.avg_index_return(index_df.loc[avg_window_mask])

    # get historical volatility
    vol_window_mask = (stock_df['date'] >= avg_start_date) & (stock_df['date'] < end_date)
    end_date_hvol = transform_stock_price.historical_volatility(stock_df[vol_window_mask], end_date)

    # get treasury yield
    treasury_mask_10yr = (treasury_10y['date'] >= avg_start_date) & (treasury_10y['date'] < end_date)
    treasury_mask_2yr = (treasury_2y['date'] >= avg_start_date) & (treasury_2y['date'] < end_date)
    previous_month_10yr = treasury_10y[treasury_mask_10yr]
    previous_month_2yr = treasury_2y[treasury_mask_2yr]
    treasury_results = transform_stock_price.treasury_yield(previous_month_10yr, previous_month_2yr, end_date)
        
    # get average vix
    vix_mask = (vix_df['date'] >= avg_start_date) & (vix_df['date'] < end_date)
    end_date_vix_df = vix_df[vix_mask]
    end_date_vix_avg = transform_stock_price.get_vix_avg(end_date_vix_df)
    end_date_vix_avg_df = pd.DataFrame([{'date': end_date, 'vix_avg': end_date_vix_avg}])

    # month index
    start_month = stock_df['date'].min() + relativedelta(years=1)
    month_index = get_month_index(start_month, end_date)

    # combine results
    index_avg_df = pd.DataFrame([{'date': end_date, 'month_index': month_index, 'index_avg': end_date_index_avg}])
    end_date_results = pd.merge(end_date_results, index_avg_df, on='date', how='inner')
    end_date_results = pd.merge(end_date_results, end_date_hvol, on=['date', 'ticker'], how='inner')
    end_date_results = pd.merge(end_date_results, treasury_results, on='date', how='inner')
    end_date_results = pd.merge(end_date_results, end_date_vix_avg_df, on='date', how='inner')

    return end_date_results

def transform_data(end_date):
    # read data
    stock_df = pd.read_csv('../files/stock_price.csv', parse_dates=['date'])
    index_df = pd.read_csv('../files/index_price.csv', parse_dates=['date'])
    vix_df = pd.read_csv('../files/vix_price.csv', parse_dates=['date'])
    sector_df = pd.read_csv('../files/company_sector.csv')
    treasury_10y = pd.read_csv('../files/treasury_yield_10yr.csv', parse_dates=['date'])
    treasury_10y= treasury_10y.ffill().bfill()
    treasury_2y = pd.read_csv('../files/treasury_yield_2yr.csv', parse_dates=['date'])
    treasury_2y= treasury_2y.ffill().bfill()
    # transform data
    stock_df = transform_stock_price.get_return(stock_df)
    index_df = transform_stock_price.get_return(index_df)
    end_month = pd.to_datetime(end_date.replace(day=1))
    # features_df = pd.DataFrame()
    features_df = latest_calculation(stock_df, index_df, treasury_10y, treasury_2y, vix_df, end_month)
    
    # get company sector
    features_df = pd.merge(features_df, sector_df, on='ticker', how='inner')
    
    # check NaN
    features_df = features_df.dropna()
    
    return features_df

if __name__ == "__main__":
    end_date = date.today().replace(day=1)
    features_df = transform_data(end_date)
    # print(features_df.head())
    json_output = '../files/json_records.json'
    features_df.to_json(json_output, orient='records')

