# optimization.py
import json
import time
import ctypes
import os
import numpy as np
from config.config import backTestConfig
from data_loader import DataLoader

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

if __name__ == "__main__":
    print("\n=== PLUTUS-CORE: IS/OOS OPTIMIZER ===")
    config = backTestConfig()
    
    # 1. Đọc khoảng tham số
    with open("parameter/optimization_parameter.json", "r") as f:
        params = json.load(f)
    MIN_W, MAX_W, IS_RATIO = params["min_window"], params["max_window"], params["in_sample_ratio"]
    
    # 2. Nạp Data và Cắt Data (Chống Overfitting)
    loader = DataLoader("raw_market_data.csv")
    prices, volumes, timestamps = loader.load_and_clean()
    split_idx = int(len(prices) * IS_RATIO)
    
    prices_IS, volumes_IS = prices[:split_idx], volumes[:split_idx]
    prices_OOS, volumes_OOS = prices[split_idx:], volumes[split_idx:]
    
    print(f"[*] Phân tách Data: In-Sample ({len(prices_IS)} nến) | Out-of-Sample ({len(prices_OOS)} nến)")
    
    # 3. Kích hoạt C++ cho In-Sample
    optimizer = CppOptimizerBridge()
    start_time = time.time()
    print(f"[*] Đang quét đa luồng từ W={MIN_W} đến {MAX_W} trên tập In-Sample...")
    
    is_results = optimizer.run_sweep(prices_IS, volumes_IS, MIN_W, MAX_W, config)
    elapsed = time.time() - start_time
    
    # Tìm ra thằng xuất sắc nhất In-Sample
    best_idx = np.argmax(is_results)
    best_window = MIN_W + best_idx
    best_is_return = is_results[best_idx]
    
    print(f"[⚡] Hoàn thành Grid Search trong {elapsed:.3f} giây!")
    print(f"[+] Tối ưu In-Sample (Quá khứ)  -> WINDOW: {best_window} | LỢI NHUẬN: {best_is_return:.2f}%")
    
    # 4. Kiểm định Out-of-Sample (Tương lai mù)
    # Ta ném đúng cái best_window đó vào C++ để test trên tập OOS
    oos_results = optimizer.run_sweep(prices_OOS, volumes_OOS, best_window, best_window, config)
    best_oos_return = oos_results[0]
    
    print(f"[+] Kiểm định Out-of-Sample -> LỢI NHUẬN: {best_oos_return:.2f}%")
    
    if best_oos_return > 0:
        print("[✓] THUẬT TOÁN ĐÃ PASS BÀI KIỂM TRA OVERFITTING!")
    else:
        print("[-] CẢNH BÁO OVERFITTING: Thuật toán rớt đài ở dữ liệu tương lai mù!")

    # 5. Lưu kết quả ra JSON
    output_data = {
        "best_window": int(best_window),
        "in_sample_return_pct": float(best_is_return),
        "out_of_sample_return_pct": float(best_oos_return),
        "status": "PASS" if best_oos_return > 0 else "OVERFITTED"
    }
    with open("parameter/optimized_parameter.json", "w") as f:
        json.dump(output_data, f, indent=4)
        
    print("[+] Đã lưu cấu hình tốt nhất vào parameter/optimized_parameter.json")