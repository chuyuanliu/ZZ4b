#include "ZZ4b/nTupleAnalysis/interface/ratioSystHistsProducer.h"
#include "assert.h"

using namespace nTupleAnalysis;
std::vector<wRSyst> ratioSystHistsProducer::systs;

ratioSystHistsProducer::ratioSystHistsProducer(const sTH1F& reference, std::string systName, std::string numTitle, std::string denomTitle): 
    reference(reference), 
    title(std::string(reference->GetName()) + '_' + systName),
    numerator((TH1F*)(reference->Clone((title + '_' + numTitle).c_str()))),
    denominator((TH1F*)(reference->Clone((title + '_' + denomTitle).c_str()))) {}

sRSyst ratioSystHistsProducer::create(const sTH1F& reference, std::string systName, std::string numTitle, std::string denomTitle){
    sRSyst rSyst(new ratioSystHistsProducer(reference, systName, numTitle, denomTitle));
    ratioSystHistsProducer::systs.push_back(wRSyst(rSyst));
    return rSyst;
}

void ratioSystHistsProducer::makeSyst(){
    if(ratio == nullptr){
        assert(!reference.expired());
        auto sRef = reference.lock();
        auto sDir = sRef->GetDirectory();
        sDir->cd();
        ratio.reset((TH1F*)(numerator->Clone((title + "_ratio").c_str())));
        ratio->Divide(denominator.get());
        up.reset((TH1F*)(ratio->Clone((title + "_up").c_str())));
        up->Multiply(sRef.get());
        down.reset((TH1F*)(ratio->Clone((title + "_down").c_str())));
        auto nbins = down->GetNbinsX() + 1;
        for(int bin = 0; bin <= nbins; ++bin){
            down->SetBinContent(bin, 2 - down->GetBinContent(bin));
        }
        down->Multiply(sRef.get());
    }
}

void ratioSystHistsProducer::makeSysts(){
    for(auto& syst:systs){
        assert(!syst.expired());
        auto sSyst = syst.lock();
        sSyst->makeSyst();
    }
}

void ratioSystHistsProducer::fill(double x, double w_num, double w_denom){
    numerator->Fill(x, w_num);
    denominator->Fill(x, w_denom);
}