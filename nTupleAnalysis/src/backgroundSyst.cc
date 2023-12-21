#include "ZZ4b/nTupleAnalysis/interface/backgroundSyst.h"

using namespace nTupleAnalysis;

const std::vector<float> backgroundSyst::bins{0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.0};

const std::map<std::string, std::vector<float>> backgroundSyst::kl{
    {"basis0", {0.029568, 0.029568, 0.029568, 0.029568, 0.029568, 0.029568, 0.029568, 0.029568, 0.029568, 0.029568, 0.029568}},
    {"basis1", {0.0359712395, 0.0026370085, -0.0257082875, -0.0463156435, -0.057138578, -0.057138578, -0.0463156435, -0.0257082875, 0.0026370085, 0.0272558755, 0.044676422}},
    {"basis2", {-0.0118843872, -0.0267221861, -0.0315855886, -0.0260324672, -0.0105933749, 0.0132461399, 0.0430985887, 0.0760989853, 0.1089755862, 0.1317893652, 0.1452654114}}};

const std::map<std::string, std::vector<float>> backgroundSyst::kVV{
    {"basis0", {0.055663, 0.055663, 0.055663, 0.055663, 0.055663, 0.055663, 0.055663, 0.055663, 0.055663, 0.055663, 0.055663}},
    {"basis1", {0.022054485, -0.0003350914, -0.0193737538, -0.0332082416, -0.040484512, -0.040484512, -0.0332082416, -0.0193737538, -0.0003350914, 0.016207482, 0.027901488}},
    {"basis2", {-0.007740774, -0.025462546, -0.031883188, -0.02640264, -0.009520952, 0.01710171, 0.050845084, 0.08840884, 0.126132612, 0.152475246, 0.168136812}}};

int backgroundSyst::getBin(float SvB)
{
    for (unsigned int i = 0; i < (bins.size() - 1); ++i)
    {
        if ((SvB >= bins.at(i)) && (SvB < bins.at(i + 1)))
            return i;
    }
    return -1;
}

bool backgroundSyst::getSyst(std::map<std::string, float> &sf, float BDT, float SvB)
{
    int bin = getBin(SvB);
    if ((bin == -1) || (BDT < -1))
    {
        sf["up_bkg_basis0"] = 1;
        sf["up_bkg_basis1"] = 1;
        sf["up_bkg_basis2"] = 1;
        sf["down_bkg_basis0"] = 1;
        sf["down_bkg_basis1"] = 1;
        sf["down_bkg_basis2"] = 1;
        return false;
    }
    auto syst = &kl;
    if (BDT < 0 && BDT >= -1)
        syst = &kVV;
    sf["up_bkg_basis0"] = 1 + syst->at("basis0").at(bin);
    sf["up_bkg_basis1"] = 1 + syst->at("basis1").at(bin);
    sf["up_bkg_basis2"] = 1 + syst->at("basis2").at(bin);
    sf["down_bkg_basis0"] = 1 - syst->at("basis0").at(bin);
    sf["down_bkg_basis1"] = 1 - syst->at("basis1").at(bin);
    sf["down_bkg_basis2"] = 1 - syst->at("basis2").at(bin);
    return true;
}