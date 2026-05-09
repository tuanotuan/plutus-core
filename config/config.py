# chua thong so cau hinh
class backTestConfig:
    INITIAL_CAPITAL = 100000.0 # von ban dau
    FEE_RATE = 0.0005 # phi giao dich tai SSI
    SLIPPAGE = 0.0 # truot gia (dung o paper trading)
    # cau hinh thuat toan VWAP
    WINDOW_SIZE = 3 # so luong tick
    NUM_THREADS = 1 # so luong thread C++ de chay VWAP engine