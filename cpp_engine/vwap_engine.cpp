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
    static void calculateChunk(const std::vector<double>& prices, const std::vector<double>& volumes, int start, int end, chunkResult& result) {
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
    static double computeVwapMultithread(const std::vector<double>& prices, const std::vector<double>& vols, int num_threads){
        int total_ticks = prices.size();
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
            threads.emplace_back(calculateChunk, std::cref(prices), std::cref(vols), start, end, std::ref(results[i]));
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
};
int main(){
    int DATA_SIZE = 1000000;
    std::vector<double> prices(DATA_SIZE, 100.0);
    std::vector<double> volumes(DATA_SIZE, 10.0);
    // lay thoi gian truc tiep tu thanh ghi cpu
    auto start_time = std::chrono::high_resolution_clock::now();
    double vwap = VWAPEngine::computeVwapMultithread(prices, volumes, 4);
    auto end_time = std::chrono::high_resolution_clock::now();
    // ep kieu nano sang ms
    std::chrono::duration<double, std::milli> elapsed = end_time - start_time;
    std::cout << "VWAP: " << vwap << std::endl;
    std::cout << "Elapsed time: " << elapsed.count() << " ms" << std::endl;
    return 0;
}