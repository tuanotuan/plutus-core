import pandas as pd
import numpy as np
import ctypes
import os
import time

class DataLoader:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_and_clean(self):
        print(f"[*] Đang nạp dữ liệu từ: {self.file_path} ...")
        df = pd.read_csv(self.file_path)
        # loai bo cac dong thieu du lieu
        df = df.dropna(subset=['Latest Matched Price', 'Latest Matched Quantity'])
        # loai bo cac dong co volume = 0 (khong tinh vao VWAP)
        df = df[df['Latest Matched Quantity'] > 0]
        print(f"[+] Dữ liệu sạch: {len(df)} ticks sẵn sàng.")
        # ep kieu va tao numpy arrays lien tuc trong RAM de truyen sang C++
        prices_np = np.ascontiguousarray(df['Latest Matched Price'].values, dtype=np.float64)
        volumes_np = np.ascontiguousarray(df['Latest Matched Quantity'].values, dtype=np.float64)
        
        return prices_np, volumes_np

class CppEngineBridge:
    def __init__(self, so_file_path="./vwap_engine.so"):
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

    def compute(self, prices_np, volumes_np, num_threads=4):
        total_ticks = len(prices_np)
        if total_ticks == 0:
            return 0.0
            
        # ep con tro tu numpy array sang con tro C
        prices_ptr = prices_np.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        volumes_ptr = volumes_np.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        
        # Gọi thẳng vào lõi C++
        return self.lib.run_vwap_engine(prices_ptr, volumes_ptr, total_ticks, num_threads)
if __name__ == "__main__":
    sample_data = {
        'Timestamp': [1632088290, 1632088291, 1632088292, 1632088293, 1632088294],
        'Latest Matched Price': [64000.0, 64005.0, np.nan, 64010.0, 63990.0], # Có 1 dòng NaN
        'Latest Matched Quantity': [0.5, 0.0, 1.2, 2.0, 0.0]                  # Có 2 dòng Volume = 0
    }
    pd.DataFrame(sample_data).to_csv("test_market_data.csv", index=False)
    # Khởi tạo Pipeline
    loader = DataLoader("test_market_data.csv")
    engine = CppEngineBridge("./cpp_engine/vwap_engine.so")

    # Pipeline Thực thi
    try:
        # Bước 1: Nạp & Lọc
        prices, volumes = loader.load_and_clean()
        
        # Bước 2: Bắn sang C++
        start_time = time.time()
        vwap_result = engine.compute(prices, volumes, num_threads=4)
        elapsed = (time.time() - start_time) * 1000 # Đổi ra ms
        
        print(f"\n[🚀] Kết quả VWAP từ C++: {vwap_result:.4f}")
        print(f"[⚡] Tốc độ xử lý: {elapsed:.3f} ms")
        
    except Exception as e:
        print(f"[!] Lỗi hệ thống: {e}")