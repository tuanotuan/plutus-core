# xu li data
import pandas as pd
import numpy as np
class DataLoader:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_and_clean(self):
        print(f"[*] Đang nạp dữ liệu từ: {self.file_path} ...")
        df = pd.read_csv(self.file_path)
        # chuyen cot Datetime sang Timestamp (int64) de truyen sang C++
        df['Timestamp'] = pd.to_datetime(df['Datetime']).astype('int64')
        # loai bo cac dong thieu du lieu
        df = df.dropna(subset=['Latest Matched Price', 'Latest Matched Quantity'])
        # loai bo cac dong co volume = 0 (khong tinh vao VWAP)
        df = df[df['Latest Matched Quantity'] > 0]
        print(f"[+] Dữ liệu sạch: {len(df)} ticks sẵn sàng.")
        # ep kieu va tao numpy arrays lien tuc trong RAM de truyen sang C++
        prices_np = np.ascontiguousarray(df['Latest Matched Price'].values, dtype=np.float64)
        volumes_np = np.ascontiguousarray(df['Latest Matched Quantity'].values, dtype=np.float64)
        # tiet kiem cpu va ram
        timestamps_np = df['Timestamp'].values

        return prices_np, volumes_np, timestamps_np