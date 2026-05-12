# noi lap rap moi thu
# main.py
import time
import pandas as pd
from config.config import backTestConfig
from data_loader import DataLoader
from backtesting import CppEngineBridge, BacktestEngine
from evaluation import Evaluator

if __name__ == "__main__":

    config = backTestConfig()
    loader = DataLoader("raw_market_data.csv")
    engine_bridge = CppEngineBridge("./cpp_engine/vwap_engine.so")

    try:
        prices, volumes, timestamps = loader.load_and_clean()
        
        backtester = BacktestEngine(engine_bridge, prices, volumes, timestamps, config)
        
        print("\n[START BACKTESTING]")
        start_time = time.time()
        trade_history = backtester.run_strategy()
        elapsed = (time.time() - start_time) * 1000
        
        print(f"\n[BACKTESTING TIME]: {elapsed:.3f} ms")
        print("\n=== TRADE LOG ===")
        if not trade_history.empty:
            print(trade_history.to_string(index=False))

            evaluator = Evaluator(trade_history, prices, timestamps, config.INITIAL_CAPITAL)
            evaluator.generate_report()
        else:
            print("Don't have any trades.")
            
    except Exception as e:
        print(f"[!] Error: {e}")