// vwap_engine.cpp
#include <iostream>
#include <vector>
#include <thread>
#include <numeric>
#include <chrono>
struct chunkResult{
    double sumpv = 0;
    double sumv = 0;
};
class VWAPEngine {
    public:
    // dung const double * de nhan thang du lieu tu RAM cua Python
    static void calculateChunk(const double *prices, const double *volumes, int start, int end, chunkResult& result) {
        double sumpv = 0;
        double sumv = 0;
        for (int i = start; i < end; ++i) {
            // luu ket qua vao thanh ghi
            sumpv += prices[i] * volumes[i];
            sumv += volumes[i];
        }
        result.sumpv = sumpv;
        result.sumv = sumv;
    }
    static double computeVwapMultithread(const double *prices, const double *volumes, int total_ticks, int num_threads){
        if(total_ticks == 0) return 0.0;
        std::vector < std::thread > threads;
        std::vector < chunkResult > results(num_threads);
        int chunk_size = total_ticks / num_threads;
        for(int i = 0; i < num_threads; i++){
            int start = i * chunk_size;
            int end = (i == num_threads - 1) ? total_ticks : (i + 1) * chunk_size;
            // perfect forwarding thay vi push_back
            // dung vo boc tham chieu de ko tu dong copy
            // ref cho phep doc va sua
            // cref chi cho phep doc, ko sua
            threads.emplace_back(calculateChunk,prices, volumes, start, end, std::ref(results[i]));
        }
        for(auto& t : threads){
            t.join();
        }
        double total_sumpv = 0;
        double total_sumv = 0;
        for(const auto& r : results){
            total_sumpv += r.sumpv;
            total_sumv += r.sumv;
        }
        return total_sumv == 0 ? 0.0 : total_sumpv / total_sumv;
    }
    static void optimizeGridSearchMultithread(
        const double* prices, const double* volumes, int total_ticks,
        int min_window, int max_window,
        double initial_capital, double fee_rate, int num_threads,
        double* out_returns
    ) {
        int num_windows = max_window - min_window + 1;
        
        auto worker = [&](int start_idx, int end_idx) {
            for (int w_idx = start_idx; w_idx < end_idx; ++w_idx) {
                int window = min_window + w_idx;
                if (window >= total_ticks) {
                    out_returns[w_idx] = 0.0;
                    continue;
                }

                double cash = initial_capital;
                double position = 0.0; 
                
                double sum_pv = 0.0;
                double sum_v = 0.0;
                for (int j = 0; j < window; ++j) {
                    sum_pv += prices[j] * volumes[j];
                    sum_v += volumes[j];
                }
                for (int i = window; i < total_ticks; ++i) {
                    // phong khi sap san
                    double vwap = (sum_v > 0) ? (sum_pv / sum_v) : prices[i-1];
                    double current_price = prices[i];

                    if (current_price > vwap && position == 0.0) {
                        position = 1.0;
                        cash -= (current_price + current_price * fee_rate);
                    } 
                    else if (current_price < vwap && position > 0.0) {
                        cash += (current_price - current_price * fee_rate);
                        position = 0.0;
                    }

                    // tinh tien cua so
                    sum_pv += (prices[i] * volumes[i]) - (prices[i - window] * volumes[i - window]);
                    sum_v += volumes[i] - volumes[i - window];
                }
                
                // liquadate cuoi ky neu con hold
                if (position > 0.0) {
                    cash += (prices[total_ticks - 1] - prices[total_ticks - 1] * fee_rate);
                }
                // ghi ket qua vao ram cua Python
                out_returns[w_idx] = ((cash - initial_capital) / initial_capital) * 100.0;
            }
        };
// load balancing cho threads
        std::vector<std::thread> threads;
        int chunk_size = num_windows / num_threads;
        int remainder = num_windows % num_threads;
        int current_start = 0;

        for (int i = 0; i < num_threads; ++i) {
            // xu li task du thua
            int current_end = current_start + chunk_size + (i < remainder ? 1 : 0);
            if (current_start < current_end) {
                threads.emplace_back(worker, current_start, current_end);
            }
            current_start = current_end;
        }

        for (auto& t : threads) {
            if(t.joinable()) t.join();
        }
    }
};
// ham nay se duoc goi tu Python, nen can dung extern "C" de tranh name mangling
// dong vai tro nhu cong giao tiep
extern "C" {
    // wvap don gian
    double run_vwap_engine(const double *prices, const double *volumes, int total_ticks, int num_threads) {
        return VWAPEngine::computeVwapMultithread(prices, volumes, total_ticks, num_threads);
    }
    // grid search toi uu hoa
    void optimize_grid_search(const double* prices, const double* volumes, int total_ticks,
        int min_window, int max_window,
        double initial_capital, double fee_rate, int num_threads,
        double* out_returns) {
        VWAPEngine::optimizeGridSearchMultithread(prices, volumes, total_ticks,
            min_window, max_window,
            initial_capital, fee_rate, num_threads,
            out_returns);
    }
}
#ifdef BUILD_TEST
int main(){
    int DATA_SIZE = 1000000;
    std::vector<double> prices(DATA_SIZE, 100.0);
    std::vector<double> volumes(DATA_SIZE, 10.0);
    // lay thoi gian truc tiep tu thanh ghi cpu
    auto start_time = std::chrono::high_resolution_clock::now();
    double vwap = VWAPEngine::computeVwapMultithread(prices.data(), volumes.data(), DATA_SIZE, 4);
    auto end_time = std::chrono::high_resolution_clock::now();
    // ep kieu nano sang ms
    std::chrono::duration<double, std::milli> elapsed = end_time - start_time;
    std::cout << "VWAP: " << vwap << std::endl;
    std::cout << "Elapsed time: " << elapsed.count() << " ms" << std::endl;
    return 0;
}
#endif