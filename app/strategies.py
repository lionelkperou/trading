import yfinance as yf
import pandas as pd
import numpy as np

def get_stock_data(symbol, start_date, end_date):
    stock = yf.Ticker(symbol)
    df = stock.history(start=start_date, end=end_date)
    return df

def bollinger_bands(df, window=20, num_std=2):
    rolling_mean = df['Close'].rolling(window=window).mean()
    rolling_std = df['Close'].rolling(window=window).std()
    df['Upper_BB'] = rolling_mean + (rolling_std * num_std)
    df['Lower_BB'] = rolling_mean - (rolling_std * num_std)
    df['BB_Signal'] = np.where(df['Close'] > df['Upper_BB'], -1, np.where(df['Close'] < df['Lower_BB'], 1, 0))
    return df

def moving_average_crossover(df, short_window=50, long_window=200):
    df['SMA_Short'] = df['Close'].rolling(window=short_window, min_periods = 1).mean()
    df['SMA_Long'] = df['Close'].rolling(window=long_window, min_periods = 1).mean()
    df['MA_Signal'] = np.where(df['SMA_Short'] > df['SMA_Long'], 1, -1)
    return df

def calculate_sharpe_ratio(returns, risk_free_rate=0.00):
    excess_returns = returns - risk_free_rate / 252  # Assuming 252 trading days in a year
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

def calculate_max_drawdown(returns):
    cumulative_returns = (1 + returns).cumprod()
    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max) / running_max
    return drawdown.min()
def calculate_returns(df):
    # Assurez-vous que les colonnes nécessaires existent
    if 'Close' not in df.columns or 'BB_Signal' not in df.columns or 'MA_Signal' not in df.columns:
        print("Colonnes manquantes dans le DataFrame")
        return df, {}

    # Calcul des rendements
    df['bb_return'] = df['Close'].pct_change() * df['BB_Signal'].shift(1)
    df['ma_return'] = df['Close'].pct_change() * df['MA_Signal'].shift(1)
    
    # Remplacer les valeurs infinies par NaN
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # Calculer les rendements cumulatifs en ignorant les NaN
    df['bb_cumulative_return'] = (1 + df['bb_return'].fillna(0)).cumprod() - 1
    df['ma_cumulative_return'] = (1 + df['ma_return'].fillna(0)).cumprod() - 1
    
    # Calculer les métriques de performance
    bb_returns = df['bb_return']
    ma_returns = df['ma_return']
    
    performance_metrics = {
        'bb_sharpe': calculate_sharpe_ratio(bb_returns) if len(bb_returns) > 0 else np.nan,
        'ma_sharpe': calculate_sharpe_ratio(ma_returns) if len(ma_returns) > 0 else np.nan,
        'bb_max_drawdown': calculate_max_drawdown(bb_returns) if len(bb_returns) > 0 else np.nan,
        'ma_max_drawdown': calculate_max_drawdown(ma_returns) if len(ma_returns) > 0 else np.nan
    }
    
    return df, performance_metrics

# Assurez-vous que ces fonctions sont également mises à jour pour gérer les NaN
def calculate_sharpe_ratio(returns, risk_free_rate=0.00):
    if len(returns) == 0:
        return np.nan
    excess_returns = returns - risk_free_rate / 252
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

def calculate_max_drawdown(returns):
    if len(returns) == 0:
        return np.nan
    cumulative_returns = (1 + returns).cumprod()
    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max) / running_max
    return drawdown.min()