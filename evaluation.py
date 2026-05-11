# evaluation.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from metrics.metric import calculate_mdd, calculate_hpr, calculate_sharpe, calculate_sortino

class Evaluator:
    def __init__(self, trade_history, prices, timestamps, initial_capital):
        self.trades = trade_history
        self.prices = prices
        self.timestamps = timestamps
        self.initial_capital = initial_capital
        
        # Đảm bảo có thư mục để nhét ảnh vào
        os.makedirs("result/backtest", exist_ok=True)

    def reconstruct_nav(self):
        """Khôi phục biến động Tổng tài sản (NAV) tại TỪNG TICK một"""
        nav_records = []
        cash = self.initial_capital
        position = 0.0
        trade_idx = 0
        num_trades = len(self.trades) if not self.trades.empty else 0
        
        for i in range(len(self.timestamps)):
            current_time = self.timestamps[i]
            current_price = self.prices[i]
            
            # Khớp thời gian với Trade Log để lật trạng thái Cash/Position
            if trade_idx < num_trades and self.trades.iloc[trade_idx]['Timestamp'] == current_time:
                action = self.trades.iloc[trade_idx]['Action']
                fee = self.trades.iloc[trade_idx]['Fee']
                
                if action == 'BUY':
                    position = 1.0
                    cash -= (current_price + fee)
                elif action in ['SELL', 'LIQUIDATE']:
                    position = 0.0
                    cash += (current_price - fee)
                trade_idx += 1
                
            # Đỉnh cao tài chính: NAV = Tiền mặt + Giá trị tài sản đang ôm tại giây phút này
            current_nav = cash + (position * current_price)
            nav_records.append(current_nav)
            
        return pd.Series(nav_records)

    def generate_report(self):
        print("\n[*] Đang chạy Động cơ Toán học đánh giá rủi ro...")
        nav_series = self.reconstruct_nav()
        returns_series = nav_series.pct_change().dropna() # Tỷ suất sinh lời theo từng tick
        
        # 1. Đo lường chỉ số
        hpr = calculate_hpr(nav_series)
        mdd, drawdown_series = calculate_mdd(nav_series)
        sharpe = calculate_sharpe(returns_series)
        sortino = calculate_sortino(returns_series)
        
        total_return = hpr.iloc[-1] * 100
        
        print("\n=== BÁO CÁO RỦI RO & HIỆU SUẤT ===")
        print(f" [✓] Tổng Lợi Nhuận (Return) : {total_return:,.2f}%")
        print(f" [✓] Maximum Drawdown (MDD)  : {mdd * 100:,.2f}%")
        print(f" [✓] Sharpe Ratio            : {sharpe:,.4f}")
        print(f" [✓] Sortino Ratio           : {sortino:,.4f}")
        
        # 2. Xuất biểu đồ HPR
        plt.figure(figsize=(10, 5))
        plt.plot(self.timestamps, hpr * 100, color="blue", linewidth=1.5)
        plt.title("Holding Period Return (HPR)")
        plt.xlabel("Thời gian")
        plt.ylabel("Tỷ suất sinh lời (%)")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.savefig("result/backtest/hpr.svg", format="svg")
        plt.close()
        
        # 3. Xuất biểu đồ Drawdown (Tô đỏ vùng sụt giảm)
        plt.figure(figsize=(10, 5))
        plt.fill_between(self.timestamps, drawdown_series * 100, 0, color="red", alpha=0.3)
        plt.plot(self.timestamps, drawdown_series * 100, color="red", linewidth=1)
        plt.title("Maximum Drawdown (MDD)")
        plt.xlabel("Thời gian")
        plt.ylabel("Độ sụt giảm (%)")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.savefig("result/backtest/drawdown.svg", format="svg")
        plt.close()
        
        print("\n[+] Đã xuất biểu đồ chuẩn báo cáo ra thư mục: result/backtest/")