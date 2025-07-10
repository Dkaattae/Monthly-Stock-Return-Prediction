import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime

def get_return(df):
    '''
    add column simple daily return to dataframe
    '''
    df['return'] = df.groupby('ticker')['price'].pct_change()
    return df

def cal_alpha_beta(stock_df, index_df, end_date):
    '''
    calulating alpha and beta according to CAPM
    this function will use column symbol, date and dailyreturn from stock_df
    column symbol, date and dailyreturn from index_df
    the window to calulating alpha and beta is set to 1 as default
    given the end_date, this function will find data within 1 year of end date,
    running simple regression be get parameters.
    returned dataframe format is 'Date' as end_date, 'Symbol' as stock ticker,
    'Beta' as CAPM beta, 'Alpha' as CAPM alpha
    '''
    return_pivot = stock_df.pivot(index='date', columns='ticker', values='return')
    spx_series = index_df.set_index('date')['return']
    return_pivot = return_pivot.ffill().bfill()
    spx_series = spx_series.reindex(return_pivot.index).ffill().bfill()
    spx_vec = return_pivot.index.to_series().map(spx_series).values
    Y = return_pivot.values
    X = spx_vec.reshape(-1, 1)
    X_design = np.hstack([np.ones_like(X), X])
    beta_matrix, _, _, _ = np.linalg.lstsq(X_design, Y, rcond=None)
    alphas = beta_matrix[0]
    betas = beta_matrix[1]

    result_df = pd.DataFrame({
        'date': end_date,
        'ticker': return_pivot.columns,
        'alpha': alphas,
        'beta': betas
    })
    return result_df

def avg_index_return(index_df):
    avg_return_num = index_df['return'].mean()
    return avg_return_num

def historical_volatility(stock_df, end_date):
    # get one month historical volatility of each stock
    stock_vol = stock_df.groupby('ticker')['return'].std()
    stock_vol.name = 'historical_vol'
    stock_vol = stock_vol.to_frame()
    stock_vol['date'] = end_date
    return stock_vol

def treasury_yield(previous_month_10yr, previous_month_2yr, end_date):
    previous_month_10yr_avg = previous_month_10yr.mean()
    eom_10yr = previous_month_10yr.iloc[-1]['DGS10']
    eom_2yr = previous_month_2yr.iloc[-1]['DGS2']
    spread = eom_10yr - eom_2yr
    return pd.DataFrame([{'date': end_date, 'eom_10yr': eom_10yr, 
                          '10yr_avg': previous_month_10yr_avg['DGS10'], 'spread': spread}])

def get_vix_avg(vix_df):
    avg_vix_num = vix_df['price'].mean()
    return avg_vix_num

def get_target(stock_df, end_date):
    price_df = stock_df.pivot(index='date', columns='ticker', values='price')
    eom_price = price_df.iloc[-1]
    bom_price = price_df.iloc[0]
    future_1m_return = (eom_price - bom_price) / bom_price
    future_1m_return.name = 'future_1m_return'
    future_1m_return = future_1m_return.to_frame()
    future_1m_return['date'] = end_date
    return future_1m_return

def rolling_calulation(stock_df, index_df, treasury_10y, treasury_2y, vix_df, min_date, max_date):
    '''
    rolling time window 
    from min_date(in data file)+1year 
    to max_date(in file)-1month or current month-1month, whichever is smaller
    calculating time window mask for each function
    apply each function, merge results
    '''
    month_starts = pd.date_range(min_date+relativedelta(years=1), 
                                 max_date-relativedelta(months=1), freq='MS')
    result_df = pd.DataFrame()
    capm_window_year = 1
    month_index = 0
    for end_date in month_starts:
        # get alpha and beta
        capm_start_date = end_date.replace(year=end_date.year - capm_window_year)
        capm_window_mask = (stock_df['date'] > capm_start_date) & (stock_df['date'] < end_date)
        capm_stock_df = stock_df.loc[capm_window_mask]
        capm_index_df = index_df.loc[capm_window_mask]
        end_date_results = cal_alpha_beta(capm_stock_df, capm_index_df, end_date)
        
        # get index average
        avg_start_date = end_date  - relativedelta(months=1)
        avg_window_mask = (index_df['date'] >= avg_start_date) & (index_df['date'] < end_date)
        end_date_index_avg = avg_index_return(index_df.loc[avg_window_mask])

        # get historical volatility
        vol_window_mask = (stock_df['date'] >= avg_start_date) & (stock_df['date'] < end_date)
        end_date_hvol = historical_volatility(stock_df[vol_window_mask], end_date)

        # get treasury yield
        treasury_mask_10yr = (treasury_10y['date'] >= avg_start_date) & (treasury_10y['date'] < end_date)
        treasury_mask_2yr = (treasury_2y['date'] >= avg_start_date) & (treasury_2y['date'] < end_date)
        previous_month_10yr = treasury_10y[treasury_mask_10yr]
        previous_month_2yr = treasury_2y[treasury_mask_2yr]
        treasury_results = treasury_yield(previous_month_10yr, previous_month_2yr, end_date)
        
        # get average vix
        vix_mask = (vix_df['date'] >= avg_start_date) & (vix_df['date'] < end_date)
        end_date_vix_df = vix_df[vix_mask]
        end_date_vix_avg = get_vix_avg(end_date_vix_df)
        end_date_vix_avg_df = pd.DataFrame([{'date': end_date, 'vix_avg': end_date_vix_avg}])
        
        # get target value
        target_mask = (stock_df['date'] >= end_date) & (stock_df['date'] < end_date + relativedelta(months=1))
        if max_date < end_date + relativedelta(months=1):
            continue
        target_df = get_target(stock_df[target_mask], end_date)

        # combine results
        index_avg_df = pd.DataFrame([{'date': end_date, 'month_index': month_index, 'index_avg': end_date_index_avg}])
        end_date_results = pd.merge(end_date_results, index_avg_df, on='date', how='inner')
        end_date_results = pd.merge(end_date_results, end_date_hvol, on=['date', 'ticker'], how='inner')
        end_date_results = pd.merge(end_date_results, treasury_results, on='date', how='inner')
        end_date_results = pd.merge(end_date_results, end_date_vix_avg_df, on='date', how='inner')
        end_date_results = pd.merge(end_date_results, target_df, on=['date', 'ticker'], how='inner')
        result_df = pd.concat([result_df, end_date_results], ignore_index=True)

        month_index += 1
    return result_df


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
    stock_df = get_return(stock_df)
    index_df = get_return(index_df)
    min_date = stock_df['date'].min()
    df_max_date = stock_df['date'].max()
    end_month = pd.to_datetime(end_date.replace(day=1))
    max_date = end_month if end_month < df_max_date else df_max_date
    # features_df = pd.DataFrame()
    features_df = rolling_calulation(stock_df, index_df, treasury_10y, treasury_2y, vix_df, min_date, max_date)
    
    # get company sector
    features_df = pd.merge(features_df, sector_df, on='ticker', how='inner')
    
    # check NaN
    features_df = features_df.dropna()
    
    return features_df


if __name__ == "__main__":
    features_df = transform_data(datetime(2025, 6, 30))
    output_file_path = '../files/features.parquet'
    features_df.to_parquet(output_file_path, engine='pyarrow')
    