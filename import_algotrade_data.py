# import_algotrade_data.py (Bản chuẩn Algotrade)
import pandas as pd
import os

def extract_standard_data(price_file, vol_file, ticker, output_path):
    print(f"[*] Đang trích xuất dữ liệu cho {ticker}...")
    chunk_size = 500000
    first_chunk = True
    
    # Đọc trực tiếp từ file CSV đã giải nén
    reader_p = pd.read_csv(price_file, chunksize=chunk_size)
    reader_v = pd.read_csv(vol_file, chunksize=chunk_size)
    
    for chunk_p, chunk_v in zip(reader_p, reader_v):
        # Lọc đúng mã (VD: VN30F2110)
        chunk_p = chunk_p[chunk_p['tickersymbol'].str.strip() == ticker]
        chunk_v = chunk_v[chunk_v['tickersymbol'].str.strip() == ticker]
        
        if chunk_p.empty: continue
            
        # Gộp Price và Volume
        merged = pd.merge(chunk_p, chunk_v, on=['datetime', 'tickersymbol'])
        
        # Format lại cột cho đúng chuẩn repo
        merged = merged.rename(columns={
            'datetime': 'datetime',
            'price': 'price',
            'quantity': 'quantity'
        })
        
        mode = 'w' if first_chunk else 'a'
        merged[['datetime', 'tickersymbol', 'price', 'quantity']].to_csv(output_path, mode=mode, index=False, header=first_chunk)
        first_chunk = False

if __name__ == "__main__":
    # Đường dẫn file CSV mày đã giải nén bằng WinRAR
    P_FILE = "algotrade_raw/quote_matched.csv"
    V_FILE = "algotrade_raw/quote_matchedvolume.csv"
    
    # Tạo thư mục theo cấu trúc repo
    os.makedirs("data/is", exist_ok=True)
    
    # Lấy dữ liệu cho tháng hiện tại (F1) và tháng kế tiếp (F2)
    # Mày chọn 2 mã tháng kề nhau từ log "10 mã đầu tiên" lúc nãy
    extract_standard_data(P_FILE, V_FILE, "VN30F2110", "data/is/VN30F1M_data.csv")
    extract_standard_data(P_FILE, V_FILE, "VN30F2111", "data/is/VN30F2M_data.csv")
    
    print("[+] XONG! Dữ liệu đã sẵn sàng trong thư mục data/is/ giống hệt repo mẫu.")