# optimization.py
import json
import time
import ctypes
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Import thêm bộ công cụ vẽ và giả lập
from config.config import backTestConfig
from data_loader import DataLoader
from backtesting import CppEngineBridge, BacktestEngine
from metrics.metric import calculate_hpr, calculate_mdd

class CppOptimizerBridge:
    def __init__(self, so_file_path="./cpp_engine/vwap_engine.so"):
        self.lib = ctypes.CDLL(os.path.abspath(so_file_path))
        self.lib.optimize_grid_search.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_double, ctypes.c_double, ctypes.c_int,
            ctypes.POINTER(ctypes.c_double)
        ]

    def run_sweep(self, prices_np, volumes_np, min_window, max_window, config):
        total_ticks = len(prices_np)
        num_windows = max_window - min_window + 1
        out_returns_np = np.zeros(num_windows, dtype=np.float64)
        
        prices_ptr = prices_np.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        volumes_ptr = volumes_np.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        out_ptr = out_returns_np.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        num_threads = os.cpu_count() or 4
        
        self.lib.optimize_grid_search(
            prices_ptr, volumes_ptr, total_ticks, min_window, max_window,
            config.INITIAL_CAPITAL, config.FEE_RATE, num_threads, out_ptr
        )
        return out_returns_np

def evaluate_and_plot_oos(trade_history, prices, timestamps, initial_capital, best_window, save_dir="result/optimization"):
    os.makedirs(save_dir, exist_ok=True)
    
    # 1. Tái tạo NAV (Tài sản ròng)
    nav_records = []
    cash = initial_capital
    position = 0.0
    trade_idx = 0
    num_trades = len(trade_history) if not trade_history.empty else 0
    
    for i in range(len(timestamps)):
        current_time = timestamps[i]
        current_price = prices[i]
        
        if trade_idx < num_trades and trade_history.iloc[trade_idx]['Timestamp'] == current_time:
            action = trade_history.iloc[trade_idx]['Action']
            fee = trade_history.iloc[trade_idx]['Fee']
            
            if action == 'BUY':
                position = 1.0
                cash -= (current_price + fee)
            elif action in ['SELL', 'LIQUIDATE']:
                position = 0.0
                cash += (current_price - fee)
            trade_idx += 1
            
        current_nav = cash + (position * current_price)
        nav_records.append(current_nav)
        
    nav_series = pd.Series(nav_records)
    
    # 2. Tính Metrics
    hpr = calculate_hpr(nav_series)
    mdd, drawdown_series = calculate_mdd(nav_series)
    
    # 3. Phục hồi và Định dạng Thời gian
    # DataLoader ép datetime sang int64 (ns), giờ ép ngược lại thành object Datetime của Pandas
    time_series = pd.to_datetime(timestamps, unit='ns') 
    
    # 4. Vẽ biểu đồ HPR
    plt.figure(figsize=(12, 6))
    plt.plot(time_series, hpr * 100, color="blue", linewidth=1.5)
    plt.title(f"Holding Period Return Over Time", fontsize=14, fontweight='bold')
    plt.xlabel("Time Step", fontsize=12)
    plt.ylabel("Percentage (%)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Ép chuẩn mốc thời gian cho trục X
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gcf().autofmt_xdate() # Xoay nghiêng chữ cho không đè lên nhau
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "hpr.svg"), format="svg")
    plt.close()
    
    # 5. Vẽ biểu đồ Drawdown
    plt.figure(figsize=(12, 6))
    plt.fill_between(time_series, drawdown_series * 100, 0, color="red", alpha=0.3)
    time_series = pd.to_datetime(timestamps, unit='ns')
    plt.plot(time_series, drawdown_series * 100, color="red", linewidth=1)
    plt.title("Drawdown Value Over Time", fontsize=14, fontweight='bold')
    plt.xlabel("Time Step", fontsize=12)
    plt.ylabel("Percentage (%)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Ép chuẩn mốc thời gian cho trục X
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "drawdown.svg"), format="svg")
    plt.close()
    
    print(f"[+] Đã xuất biểu đồ HPR và Drawdown (trục thời gian chuẩn) vào: {save_dir}/")

if __name__ == "__main__":
    print("\n=== PLUTUS-CORE: IS/OOS OPTIMIZER ===")
    config = backTestConfig()
    
    with open("parameter/optimization_parameter.json", "r") as f:
        params = json.load(f)
    MIN_W, MAX_W, IS_RATIO = params["min_window"], params["max_window"], params["in_sample_ratio"]
    
    loader = DataLoader("data/is/VN30F1M_data.csv")
    prices, volumes, timestamps = loader.load_and_clean()
    split_idx = int(len(prices) * IS_RATIO)
    
    # Đã cắt 30% cuối cùng cho OOS
    prices_IS, volumes_IS, timestamps_IS = prices[:split_idx], volumes[:split_idx], timestamps[:split_idx]
    prices_OOS, volumes_OOS, timestamps_OOS = prices[split_idx:], volumes[split_idx:], timestamps[split_idx:]
    
    print(f"[*] Phân tách Data: In-Sample ({len(prices_IS)} nến) | Out-of-Sample ({len(prices_OOS)} nến)")
    
    optimizer = CppOptimizerBridge()
    start_time = time.time()
    print(f"[*] Đang quét đa luồng từ W={MIN_W} đến {MAX_W} trên tập In-Sample...")
    
    is_results = optimizer.run_sweep(prices_IS, volumes_IS, MIN_W, MAX_W, config)
    elapsed = time.time() - start_time
    
    best_idx = np.argmax(is_results)
    best_window = MIN_W + best_idx
    best_is_return = is_results[best_idx]
    
    print(f"[⚡] Hoàn thành Grid Search trong {elapsed:.3f} giây!")
    print(f"[+] Tối ưu In-Sample (Quá khứ)  -> WINDOW: {best_window} | LỢI NHUẬN: {best_is_return:.2f}%")
    
    oos_results = optimizer.run_sweep(prices_OOS, volumes_OOS, best_window, best_window, config)
    best_oos_return = oos_results[0]
    
    print(f"[+] Kiểm định Out-of-Sample -> LỢI NHUẬN: {best_oos_return:.2f}%")
    
    if best_oos_return > 0:
        print("[✓] THUẬT TOÁN ĐÃ PASS BÀI KIỂM TRA OVERFITTING!")
    else:
        print("[-] CẢNH BÁO OVERFITTING: Thuật toán rớt đài ở dữ liệu tương lai mù!")

    print(f"[*] Đang tái tạo giao dịch Out-of-Sample để vẽ biểu đồ...")
    config.WINDOW_SIZE = int(best_window) 
    engine_bridge = CppEngineBridge("./cpp_engine/vwap_engine.so")
    
    # Chỉ bơm 30% Data cuối cùng vào BacktestEngine
    backtester_oos = BacktestEngine(engine_bridge, prices_OOS, volumes_OOS, timestamps_OOS, config)
    trade_history_oos = backtester_oos.run_strategy()
    
    # Chỉ truyền Timestamp của 30% cuối vào hệ thống vẽ
    evaluate_and_plot_oos(trade_history_oos, prices_OOS, timestamps_OOS, config.INITIAL_CAPITAL, int(best_window))

    output_data = {
        "best_window": int(best_window),
        "in_sample_return_pct": float(best_is_return),
        "out_of_sample_return_pct": float(best_oos_return),
        "status": "PASS" if best_oos_return > 0 else "OVERFITTED"
    }
    with open("parameter/optimized_parameter.json", "w") as f:
        json.dump(output_data, f, indent=4)
        
    print("[+] Đã lưu cấu hình tốt nhất vào parameter/optimized_parameter.json")