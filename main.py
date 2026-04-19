import asyncio
import websockets
import json

# URL kết nối gộp 2 luồng: Sổ lệnh (Depth) và Khớp lệnh (Trade) của cặp BTC/USDT
BINANCE_WS_URL = "wss://fstream.binance.com/stream?streams=btcusdt@depth20@100ms/btcusdt@aggTrade"

async def binance_data_stream():
    """Hàm bất đồng bộ (async) để duy trì kết nối WebSocket"""
    print(f"[*] Bắt đầu kết nối tới Binance Futures...")
    
    # Mở ống nước kết nối
    async with websockets.connect(BINANCE_WS_URL) as websocket:
        print("[+] Kết nối thành công! Đang hứng luồng dữ liệu siêu tốc...\n" + "-"*50)
        
        try:
            while True:
                # Lắng nghe dữ liệu đẩy về (Không block CPU nhờ từ khóa await)
                message = await websocket.recv()
                
                # Chuyển string JSON thành Dictionary của Python
                data = json.loads(message)
                
                # Phân loại luồng dữ liệu (Multiplexing)
                stream_name = data.get('stream')
                payload = data.get('data')
                
                if "depth" in stream_name:
                    # Lấy giá Mua cao nhất (Bid) và Bán thấp nhất (Ask)
                    best_bid = payload['b'][0][0]
                    best_ask = payload['a'][0][0]
                    print(f"[ORDER BOOK] Bid: {best_bid} | Ask: {best_ask}")
                    
                elif "aggTrade" in stream_name:
                    # p: Price, q: Quantity, m: Is the buyer the market maker? (True = Lệnh Bán chủ động đập vào, False = Lệnh Mua chủ động đập vào)
                    price = payload['p']
                    qty = payload['q']
                    side = "BÁN" if payload['m'] else "MUA"
                    print(f"    [TRADE] ---> Khớp {side}: {qty} BTC tại giá {price}")
                    
        except websockets.ConnectionClosed:
            print("[-] Kết nối đã bị đóng từ phía server.")
        except Exception as e:
            print(f"[!] Lỗi đột xuất: {e}")

if __name__ == "__main__":
    # Khởi động Event Loop của Python để chạy hàm async
    try:
        asyncio.run(binance_data_stream())
    except KeyboardInterrupt:
        print("\n[*] Đã dừng luồng dữ liệu thủ công.")