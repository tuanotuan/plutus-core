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
        }
    }
};
int main(){
    return 0;
}