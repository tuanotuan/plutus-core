import asyncio
import websockets
import json
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS

# --- CẤU HÌNH HỆ THỐNG ---
BINANCE_WS_URL = "wss://fstream.binance.com/stream?streams=btcusdt@depth20@100ms/btcusdt@aggTrade"
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "Vp5BKeVg4s5jY8z4VY9JodS6nr2EpMtEV7crxq3w7dwY-XIGj8hoAIS90c-9OpyYNc1mMgCAKUstq61Y4EMSzg=="
INFLUX_ORG = "algotrade"
INFLUX_BUCKET = "market_data"

# Vùng đệm dữ liệu (Cái xô chứa tối đa 10,000 tin nhắn để tránh tràn RAM)
data_queue = asyncio.Queue(maxsize=10000)

async def websocket_producer():
    """Luồng 1: Hứng data từ Binance và ném vào Queue (Vùng đệm)"""
    print("[*] Producer: Đang kết nối WebSocket tới Binance...")
    async with websockets.connect(BINANCE_WS_URL) as websocket:
        print("[+] Producer: Kết nối thành công! Đang hứng dữ liệu...\n" + "-"*50)
        try:
            while True:
                message = await websocket.recv()
                # Ném data vào queue. Nếu queue đầy, nó sẽ tự động nghẽn lại chờ (backpressure)
                await data_queue.put(message)
        except websockets.ConnectionClosed:
            print("[-] Producer: Kết nối đã bị đóng từ phía server.")
        except Exception as e:
            print(f"[!] Producer Lỗi: {e}")

async def influx_consumer():
    """Luồng 2: Bốc data từ Queue và ghi vào InfluxDB theo Batch (Gom nhóm)"""
    # Khởi tạo client kết nối DB
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    # Kích hoạt chế độ ghi bất đồng bộ chạy ngầm (tránh block CPU)
    write_api = client.write_api(write_options=ASYNCHRONOUS)
    
    print("[*] Consumer: Hệ thống ghi cơ sở dữ liệu đã sẵn sàng...")
    
    batch = []
    batch_size = 500  # Gom đủ 500 dòng tick rồi mới ghi 1 lần xuống ổ cứng
    last_flush_time = time.time()

    while True:
        # Lấy message từ queue ra để xử lý
        message = await data_queue.get()
        data = json.loads(message)
        
        stream_name = data.get('stream')
        payload = data.get('data')
        
        # Chuyển đổi dữ liệu chuỗi thành đối tượng Point (Định dạng chuẩn của InfluxDB)
        point = None
        if "depth" in stream_name:
            # Lưu sổ lệnh (Orderbook)
            point = Point("orderbook") \
                .tag("symbol", "BTCUSDT") \
                .field("bid", float(payload['b'][0][0])) \
                .field("ask", float(payload['a'][0][0]))
        elif "aggTrade" in stream_name:
            # Lưu lịch sử khớp lệnh thực tế (Trades)
            point = Point("trades") \
                .tag("symbol", "BTCUSDT") \
                .tag("side", "SELL" if payload['m'] else "BUY") \
                .field("price", float(payload['p'])) \
                .field("qty", float(payload['q']))

        if point:
            batch.append(point)

        # ĐIỀU KIỆN ĐỔ XÔ (FLUSH):
        # 1. Nếu gom đủ 500 dòng HOẶC
        # 2. Đã quá 1 giây trôi qua mà chưa ghi (tránh kẹt data lúc ít người giao dịch)
        current_time = time.time()
        if len(batch) >= batch_size or (current_time - last_flush_time > 1):
            if batch:
                write_api.write(bucket=INFLUX_BUCKET, record=batch)
                print(f"[DB] Đã xả thành công {len(batch)} dòng xuống InfluxDB. (Queue đang chờ: {data_queue.qsize()})")
                batch = []
                last_flush_time = current_time
        
        # Báo cáo cho Queue biết là đã xử lý xong tin nhắn này
        data_queue.task_done()

async def main():
    # Khởi chạy song song cả 2 luồng Producer và Consumer
    await asyncio.gather(
        websocket_producer(),
        influx_consumer()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Đã nhận lệnh ngắt. Hệ thống Data Ingestion đã dừng an toàn.")