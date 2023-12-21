#include <vector>
#include <map>
#include <string>

namespace nTupleAnalysis
{
    class backgroundSyst
    {
    public:
        static const std::vector<float> bins;
        static const std::map<std::string, std::vector<float>> kl;
        static const std::map<std::string, std::vector<float>> kVV;

        static int getBin(float SvB);
        static bool getSyst(std::map<std::string, float> &sf, float BDT, float SvB);
    };
}