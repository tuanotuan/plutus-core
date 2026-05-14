# evaluation.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from metrics.metric import calculate_mdd, calculate_hpr, calculate_sharpe, calculate_sortino

class Evaluator:
    def __init__(self, trade_history, prices, timestamps, initial_capital):
        self.trades = trade_history
        self.prices = prices
        self.timestamps = timestamps
        self.initial_capital = initial_capital
        # exist_ok = true, tao thu muc neu chua co
        os.makedirs("result/backtest", exist_ok=True)

    def reconstruct_nav(self):
        # bien dong nav = tien mat + gia tri tai san dang om
        nav_records = []
        cash = self.initial_capital
        position = 0.0
        trade_idx = 0
        num_trades = len(self.trades) if not self.trades.empty else 0
        
        for i in range(len(self.timestamps)):
            current_time = self.timestamps[i]
            current_price = self.prices[i]
            
            # two - pointer: di qua lich su giao dich va cap nhat position + cash theo tung tick
            if trade_idx < num_trades and self.trades.iloc[trade_idx]['Timestamp'] == current_time:
                action = self.trades.iloc[trade_idx]['Action']
                fee = self.trades.iloc[trade_idx]['Fee']
                
                if action == 'BUY':
                    position = 1.0
                    cash -= (current_price + fee)
                elif action in ['SELL', 'LIQUIDATE']: #liquidate, bat buoc phai ban het tai san dang om
                    position = 0.0
                    cash += (current_price - fee)
                trade_idx += 1
                
            current_nav = cash + (position * current_price)
            nav_records.append(current_nav)
            
        return pd.Series(nav_records)

    def generate_report(self):
        # giai thich: reconstruct_nav() se duoc goi de tinh toan NAV theo tung tick
        # sau do su dung cac ham metric de tinh toan chi so hpr, mdd, sharpe, sortino.
        nav_series = self.reconstruct_nav()
        returns_series = nav_series.pct_change().dropna() # ty suat sinh loi theo tung tick
        
        # 1. Đo lường chỉ số
        hpr = calculate_hpr(nav_series)
        mdd, drawdown_series = calculate_mdd(nav_series)
        sharpe = calculate_sharpe(returns_series)
        sortino = calculate_sortino(returns_series)
        # loi nhuan chot so
        total_return = hpr.iloc[-1] * 100
        
        print("\n=== BÁO CÁO RỦI RO & HIỆU SUẤT ===")
        print(f" [✓] Tổng Lợi Nhuận (Return) : {total_return:,.2f}%")
        print(f" [✓] Maximum Drawdown (MDD)  : {mdd * 100:,.2f}%")
        print(f" [✓] Sharpe Ratio            : {sharpe:,.4f}")
        print(f" [✓] Sortino Ratio           : {sortino:,.4f}")
        
        # bieu do hpr
        plt.figure(figsize=(10, 5))
        time_series = pd.to_datetime(self.timestamps, unit='ns')
        plt.plot(time_series, hpr * 100, color="blue", linewidth=1.5)
        plt.title("Holding Period Return Over Time")
        plt.xlabel("Time Step")
        plt.ylabel("Holding Period Return (%)")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.savefig("result/backtest/hpr.svg", format="svg")
        plt.close()
        
        # bieu do mdd
        plt.figure(figsize=(10, 5))
        plt.fill_between(time_series, drawdown_series * 100, 0, color="red", alpha=0.3)
        plt.plot(time_series, drawdown_series * 100, color="red", linewidth=1)
        plt.title("Draw down Value Over Time")
        plt.xlabel("Time Step")
        plt.ylabel("Percentage (%)")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gcf().autofmt_xdate()
        plt.savefig("result/backtest/drawdown.svg", format="svg")
        plt.close()