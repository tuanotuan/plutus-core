# loi giao dich va goi C++ engine de tinh VWAP
# backtesting.py
import ctypes
import os
import pandas as pd
class CppEngineBridge:
    def __init__(self, so_file_path="./cpp_engine/vwap_engine.so"):
        # anh xa file .so vao Python
        self.lib = ctypes.CDLL(os.path.abspath(so_file_path))
        
        # Định nghĩa kiểu dữ liệu truyền vào và trả về cho hàm run_vwap_engine
        self.lib.run_vwap_engine.argtypes = [
            ctypes.POINTER(ctypes.c_double), # double* prices
            ctypes.POINTER(ctypes.c_double), # double* volumes
            ctypes.c_int,                    # int total_ticks
            ctypes.c_int                     # int num_threads
        ]
        self.lib.run_vwap_engine.restype = ctypes.c_double

    def compute(self, prices_np, volumes_np, num_threads):
        total_ticks = len(prices_np)
        if total_ticks == 0:
            return 0.0
        # ep con tro tu numpy array sang con tro C
        prices_ptr = prices_np.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        volumes_ptr = volumes_np.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        
        # goi loi C++ engine de tinh VWAP va tra ve ket qua
        return self.lib.run_vwap_engine(prices_ptr, volumes_ptr, total_ticks, num_threads)
class BacktestEngine:
    def __init__(self, engine_bridge, prices, volumes, timestamps, config):
        self.engine = engine_bridge
        self.prices = prices
        self.volumes = volumes
        self.timestamps = timestamps
        self.config = config
        
        self.cash = self.config.INITIAL_CAPITAL
        # long - only
        # position = 0.0: chua co lenh, 1.0: da mua, -1.0: da ban (short)
        self.position = 0.0 
        self.trade_log = [] 
        
    def run_strategy(self):
        window = self.config.WINDOW_SIZE
        total_ticks = len(self.prices)
        
        if total_ticks <= window:
            print("[-] Dữ liệu quá ngắn.")
            return pd.DataFrame()
            
        for i in range(window, total_ticks):
            
            # du lieu qua khu de tinh VWAP (chua bao gom tick hien tai)
            # tinh tu dong 0 den i-1, co do dai bang window size
            slice_prices = self.prices[i-window : i]
            slice_volumes = self.volumes[i-window : i]
            
            # trung binh qua khu de tinh VWAP, goi C++ engine
            current_vwap = self.engine.compute(slice_prices, slice_volumes, self.config.NUM_THREADS)
            current_price = self.prices[i]
            current_time = self.timestamps[i]
            
            # giua vao current_price va current_vwap de quyet dinh mua ban
            if current_price > current_vwap and self.position == 0:
                self.position = 1.0 
                fee = current_price * self.config.FEE_RATE
                self.cash -= (current_price + fee)
                self.trade_log.append({
                    'Timestamp': current_time, 'Action': 'BUY', 
                    'Price': current_price, 'Fee': fee, 'PnL': 0.0
                })
                
            elif current_price < current_vwap and self.position > 0:
                fee = current_price * self.config.FEE_RATE
                self.cash += (current_price - fee)
                
                entry_price = self.trade_log[-1]['Price']
                profit = (current_price - entry_price) - fee - self.trade_log[-1]['Fee']
                
                self.trade_log.append({
                    'Timestamp': current_time, 'Action': 'SELL', 
                    'Price': current_price, 'Fee': fee, 'PnL': profit
                })
                self.position = 0.0 
                
        return pd.DataFrame(self.trade_log)