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
};
int main(){
    return 0;
}