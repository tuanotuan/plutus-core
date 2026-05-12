# cao du lieu tu Binance
import requests
import pandas as pd
import time

def fetch_binance_data(symbol="BTCUSDT", interval="1m", pages=10):
    print(f"[*] Đang cào dữ liệu THÔ {symbol} từ API của Binance...")
    start_time = time.time()
    
    all_data = []
    end_time = None
    limit = 1000 # max limit / request
    
    for i in range(pages):
        url = "https://api4.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if end_time:
            params["endTime"] = end_time
            
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            if not data:
                break
            
            all_data = data + all_data 
            
            end_time = data[0][0] - 1 
            print(f"  -> Đã tải gói {i+1}/{pages} ({len(data)} nến)")
            time.sleep(0.5) # tranh binance block do request qua nhanh
            
        except Exception as e:
            print(f"[-] Error Connecting to Binance: {e}")
            break

    if not all_data:
        print("[-] Error: Don't have any data!")
        return

    df = pd.DataFrame(all_data, columns=[
        "Open_time", "Open", "High", "Low", "Close", "Volume",
        "Close_time", "Quote_asset_volume", "Number_of_trades",
        "Taker_buy_base", "Taker_buy_quote", "Ignore"
    ])
    
    # chuyen doi kieu du lieu
    df['Datetime'] = pd.to_datetime(df['Open_time'], unit='ms')
    
    df = df[['Datetime', 'Close', 'Volume']]
    
    output_file = "raw_market_data.csv"
    df.to_csv(output_file, index=False)
    
    elapsed = time.time() - start_time
    print(f"\n[+] Đã đổ {len(df)} dòng dữ liệu THÔ vào {output_file} (Thời gian: {elapsed:.2f}s)")

if __name__ == "__main__":
    fetch_binance_data()