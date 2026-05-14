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
        df['Timestamp'] = pd.to_datetime(df['datetime']).astype('int64')
        # loai bo cac dong thieu du lieu
        df = df.dropna(subset=['price', 'quantity'])
        # loai bo cac dong co volume = 0 (khong tinh vao VWAP)
        df = df[df['quantity'] > 0]
        df = df.sort_values(by='Timestamp', ascending=True).reset_index(drop=True)
        print(f"[+] Dữ liệu sạch: {len(df)} ticks sẵn sàng.")
        # ep kieu va tao numpy arrays lien tuc trong RAM de truyen sang C++
        prices_np = np.ascontiguousarray(df['price'].values, dtype=np.float64)
        volumes_np = np.ascontiguousarray(df['quantity'].values, dtype=np.float64)
        # tiet kiem cpu va ram
        timestamps_np = df['Timestamp'].values

        return prices_np, volumes_np, timestamps_np