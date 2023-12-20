#if !defined(ratioSystHistsProducer_H)
#define ratioSystHistsProducer_H
#include <TH1F.h>
#include <TDirectory.h>
#include <vector>

namespace nTupleAnalysis
{
    class ratioSystHistsProducer;
    typedef std::shared_ptr<ratioSystHistsProducer> sRSyst;
    typedef std::weak_ptr<ratioSystHistsProducer> wRSyst;

    typedef std::shared_ptr<TH1F> sTH1F;
    typedef std::weak_ptr<TH1F> wTH1F;

    class ratioSystHistsProducer
    {
    private:
        const wTH1F reference;
        const std::string title;
        sTH1F numerator;
        sTH1F denominator;

        sTH1F ratio;
        sTH1F up;
        sTH1F down;

        static std::vector<wRSyst> systs;

        ratioSystHistsProducer(const sTH1F &reference, std::string systName, std::string numTitle, std::string denomTitle);
        void makeSyst();

    public:
        [[nodiscard]] static sRSyst create(const sTH1F &reference, std::string systName, std::string numTitle = "num", std::string denomTitle = "denom");
        static void makeSysts();
        void Fill(double x, double w_num, double w_denom);
    };
}
#endif // ratioSystHistsProducer_H
