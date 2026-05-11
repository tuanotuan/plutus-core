# metrics/metric.py
import numpy as np
import pandas as pd
#hpr = (tong tai san hien tai - von) / von
def calculate_hpr(nav_series):
    initial_nav = nav_series.iloc[0]
    return (nav_series - initial_nav) / initial_nav

def calculate_mdd(nav_series):
    rolling_max = nav_series.cummax()
    drawdown = (nav_series - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    return max_drawdown, drawdown

def calculate_sharpe(returns_series, risk_free_rate=0.0):
    # .std tra ve do lech chuan
    if len(returns_series) == 0 or returns_series.std() == 0:
        return 0.0
    return (returns_series.mean() - risk_free_rate) / returns_series.std()

def calculate_sortino(returns_series, risk_free_rate=0.0):
    if len(returns_series) == 0:
        return 0.0
    downside_returns = returns_series[returns_series < 0]
    
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0.0
    return (returns_series.mean() - risk_free_rate) / downside_returns.std()