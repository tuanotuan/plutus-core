# import_algotrade_data.py
# vibe code
import pandas as pd
import os
import time

def extract_and_join(price_file, vol_file, f1_ticker, f2_ticker):
    target_tickers = [f1_ticker, f2_ticker]
    
    if not os.path.exists(price_file) or not os.path.exists(vol_file):
        print(f"Not found {price_file} or {vol_file}. Please check the paths.")
        return
    price_chunks = []
    chunk_count = 0
    for chunk in pd.read_csv(price_file, chunksize=1000000, low_memory=False):
        chunk_count += 1
        chunk['tickersymbol'] = chunk['tickersymbol'].astype(str).str.strip().str.upper()
        filtered = chunk[chunk['tickersymbol'].isin(target_tickers)]
        if not filtered.empty:
            price_chunks.append(filtered)
        if chunk_count % 5 == 0:
            print(f"  -> Đã quét {chunk_count} củ dòng...")
            
    df_price = pd.concat(price_chunks, ignore_index=True) if price_chunks else pd.DataFrame()
    print(f"[+] Hoàn thành Phase 1. Gom được {len(df_price):,} tick Giá vào RAM.")
    vol_chunks = []
    chunk_count = 0
    for chunk in pd.read_csv(vol_file, chunksize=1000000, low_memory=False):
        chunk_count += 1
        chunk['tickersymbol'] = chunk['tickersymbol'].astype(str).str.strip().str.upper()
        filtered = chunk[chunk['tickersymbol'].isin(target_tickers)]
        if not filtered.empty:
            vol_chunks.append(filtered)
        if chunk_count % 5 == 0:
            print(f"  -> Đã quét {chunk_count} củ dòng...")
            
    df_vol = pd.concat(vol_chunks, ignore_index=True) if vol_chunks else pd.DataFrame()
    print(f"[+] Hoàn thành Phase 2. Gom được {len(df_vol):,} tick Khối lượng vào RAM.")

    if df_price.empty or df_vol.empty:
        print("[-] LỖI CHÍ MẠNG: 1 trong 2 mỏ bị rỗng. Không có điểm chung để ghép!")
        return

    print("\n[*] PHASE 3: Đang ghép mạch (Merge) trong RAM...")
    merged = pd.merge(df_price, df_vol, on=['datetime', 'tickersymbol'])
    
    merged = merged.rename(columns={
        'datetime': 'datetime',
        'price': 'price',
        'quantity': 'quantity'
    })
    
    os.makedirs("data/is", exist_ok=True)
    
    # Chia phe F1 và F2
    f1_data = merged[merged['tickersymbol'] == f1_ticker]
    f2_data = merged[merged['tickersymbol'] == f2_ticker]
    
    f1_path = "data/is/VN30F1M_data.csv"
    f2_path = "data/is/VN30F2M_data.csv"
    
    f1_data[['datetime', 'tickersymbol', 'price', 'quantity']].to_csv(f1_path, index=False)
    f2_data[['datetime', 'tickersymbol', 'price', 'quantity']].to_csv(f2_path, index=False)
    
    print(f"\n[+] XUẤT SẮC! Đã nhả {len(f1_data):,} tick vào {f1_path}")
    print(f"[+] XUẤT SẮC! Đã nhả {len(f2_data):,} tick vào {f2_path}")

if __name__ == "__main__":
    P_FILE = "algotrade_raw/quote_matched.csv"
    V_FILE = "algotrade_raw/quote_matchedvolume.csv"
    
    F1 = "VN30F2110"
    F2 = "VN30F2111"
    
    start_time = time.time()
    extract_and_join(P_FILE, V_FILE, F1, F2)
    print(f"\n[*] TỔNG THỜI GIAN CÀY NÁT 5GB DATA: {time.time() - start_time:.2f}s")