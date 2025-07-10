import yfinance as yf
import datetime
import pandas as pd
import pytz
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import pandas_datareader.data as web

def download_stock_price(stock_tickers, start_date, end_date):
    # Download data for all tickers

    stock_data = yf.download(stock_tickers, start=start_date, end=end_date, auto_adjust=True) 

    # Extract adjusted close prices
    adj_close_prices = stock_data['Close']
    adj_close_prices.reset_index(inplace=True)
    df_unpivot = pd.melt(adj_close_prices, col_level=0, id_vars=['Date'], value_vars=adj_close_prices.columns.tolist())
    price_df = df_unpivot.rename(columns={'value': 'price', 'Ticker': 'ticker', 'Date': 'date'})
    price_filename = '../files/stock_price.csv'
    price_df.to_csv(price_filename, columns=['date', 'ticker', 'price'], index=False)

    return start_date.replace('-', '')

def download_index_price(start_date, end_date):
    index_data = yf.download("^GSPC", start=start_date, end=end_date, auto_adjust=True)

    adj_close_prices = index_data['Close']
    adj_close_prices.reset_index(inplace=True)
    index_price = adj_close_prices.rename(columns={'Date': 'date', '^GSPC': 'price'})
    index_price['ticker'] = 'SPX'

    index_filename = '../files/index_price.csv'
    index_price.to_csv(index_filename, columns=['date', 'ticker', 'price'], index=False)

    return start_date.replace('-', '')

def download_vix_price(start_date, end_date):
    index_data = yf.download("^VIX", start=start_date, end=end_date, auto_adjust=True)

    adj_close_prices = index_data['Close']
    adj_close_prices.reset_index(inplace=True)
    index_price = adj_close_prices.rename(columns={'Date': 'date', '^VIX': 'price'})
    index_price['ticker'] = 'VIX'

    index_filename = '../files/vix_price.csv'
    index_price.to_csv(index_filename, columns=['date', 'ticker', 'price'], index=False)

    return start_date.replace('-', '')

def download_company_sector(company_list):
    company_sector = []
    for ticker in company_list:
        stocks = yf.Ticker(ticker)
        sector = stocks.info.get('sector', 'N/A')
        company_sector.append({'ticker': ticker, 'sector': sector})
    company_sector_path = '../files/company_sector.csv'
    pd.DataFrame(company_sector).to_csv(company_sector_path, columns=['ticker', 'sector'], index=False)
    return company_sector

def download_treasury_yield(start_date, end_date, maturity):
    field = f'DGS{maturity}'
    treasury_yield = web.DataReader(field, "fred", start_date, end_date)
    treasury_yield.reset_index(inplace=True)
    treasury_yield = treasury_yield.rename(columns={'DATE': 'date'})
    yield_path = f'../files/treasury_yield_{maturity}yr.csv'
    treasury_yield.to_csv(yield_path, columns=['date', field], index=False)
    return treasury_yield

def download_data(data_span, ticker_file_path):
    ct = datetime.datetime.now(pytz.timezone('America/New_York'))
    if ct.hour >= 16:
        current_date = ct.strftime('%Y-%m-%d')
    else:
        current_date = (ct - timedelta(days=1)).strftime('%Y-%m-%d')
    # List of stock tickers
    ticker_df = pd.read_csv(ticker_file_path)
    stock_tickers = ticker_df['Symbol'].tolist()
    price_start = (ct - relativedelta(years=data_span)).strftime('%Y-%m-01')
    index_start = (ct - relativedelta(years=data_span)).strftime('%Y-%m-01')
    vix_start = (ct - relativedelta(years=data_span)).strftime('%Y-%m-01')
    price_data = download_stock_price(stock_tickers, price_start, current_date)
    index_data = download_index_price(index_start, current_date)
    vix_data = download_vix_price(vix_start, current_date)
    company_sector = download_company_sector(stock_tickers)
    treasury_10y = download_treasury_yield(index_start, current_date, 10)
    treasury_2y = download_treasury_yield(index_start, current_date, 2)
    
    return None


if __name__ == "__main__":
    download_data(data_span=3, ticker_file_path='../files/spx_tickers.csv')