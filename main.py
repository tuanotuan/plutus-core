# noi lap rap moi thu
# main.py
import time
import pandas as pd
from config.config import backTestConfig
from data_loader import DataLoader
from backtesting import CppEngineBridge, BacktestEngine

if __name__ == "__main__":
    # 1. Tạo data giả lập (Cứ để đây để test cho tiện)
    sample_data = {
        'Timestamp': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        'Latest Matched Price':    [64000, 64005, 64010, 64050, 63900, 63800, 64200, 64300, 63500, 63400, 64500], 
        'Latest Matched Quantity': [1.0,   1.5,   2.0,   1.0,   2.5,   1.0,   3.0,   1.0,   4.0,   1.0,   2.0]
    }
    pd.DataFrame(sample_data).to_csv("test_market_data.csv", index=False)

    # 2. Lắp ráp các Module
    config = backTestConfig()
    loader = DataLoader("test_market_data.csv")
    engine_bridge = CppEngineBridge("./cpp_engine/vwap_engine.so")

    try:
        # 3. Chạy Pipeline
        prices, volumes, timestamps = loader.load_and_clean()
        
        backtester = BacktestEngine(engine_bridge, prices, volumes, timestamps, config)
        
        print("\n[BẮT ĐẦU BACKTEST]")
        start_time = time.time()
        trade_history = backtester.run_strategy()
        elapsed = (time.time() - start_time) * 1000
        
        # 4. In Báo cáo
        print(f"\n[⚡] Thời gian hoàn thành: {elapsed:.3f} ms")
        print("\n=== NHẬT KÝ GIAO DỊCH ===")
        print(trade_history.to_string(index=False) if not trade_history.empty else "Không có giao dịch.")
        print(f"\n[💰] SỐ DƯ CUỐI CÙNG: ${backtester.cash:,.2f}")
            
    except Exception as e:
        print(f"[!] Lỗi: {e}")