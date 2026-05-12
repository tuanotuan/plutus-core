# cao data tu yahoo finance trong 7 ngay gan nhat, voi do phan giai 1 phut
import yfinance as yf
import pandas as pd
import time

def fetch_raw_data(symbol="BTC-USD", period="7d", interval="1m"):
    print(f"[*] Đang cào dữ liệu THÔ {symbol} từ Yahoo Finance...")
    start_time = time.time()
    
    data = yf.download(symbol, period=period, interval=interval, progress=False)
    
    if data.empty:
        print("[-] Lỗi: Không tải được dữ liệu!")
        return
        
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        
    data.reset_index(inplace=True)
    
    output_file = "raw_market_data.csv"
    data.to_csv(output_file, index=False)
    
    elapsed = time.time() - start_time
    print(f"[+] Đã đổ {len(data)} dòng dữ liệu THÔ vào {output_file} (Thời gian: {elapsed:.2f}s)")

if __name__ == "__main__":
    fetch_raw_data()