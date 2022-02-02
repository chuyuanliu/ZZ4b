#include "ZZ4b/nTupleAnalysis/interface/dump.h"
#include <iostream>

namespace nTupleAnalysis::dump{
    const char* dumpBranch::leafname()
    {
        return (name + "/" + type).c_str();
    }
    template<typename T>
    void dumpBranch::init()
    {
        value = new T;
    }
    template<typename T>
    void dumpBranch::clean()
    {
        delete static_cast<T*>(value);
    }

    dumpRoot::dumpRoot(const std::string &path)
    {
        if(path != "")
        {   
            std::cout<<path<<std::endl;
            rootFile = TFile::Open(path.c_str(), "RECREATE");
            rootTree = new TTree("Events", "");
            variables["weight"]  = std::make_shared<dumpBranch>("weight", 'F');
            variables["VpT"]     = std::make_shared<dumpBranch>("V_pt", 'F');
            variables["H1m"]     = std::make_shared<dumpBranch>("VHH_H1_m", 'F');
            variables["H1E"]     = std::make_shared<dumpBranch>("VHH_H1_e", 'F');
            variables["H1pT"]    = std::make_shared<dumpBranch>("VHH_H1_pT", 'F');
            variables["H1eta"]   = std::make_shared<dumpBranch>("VHH_H1_eta", 'F');
            variables["H2m"]     = std::make_shared<dumpBranch>("VHH_H2_m", 'F');
            variables["H2E"]     = std::make_shared<dumpBranch>("VHH_H2_e", 'F');
            variables["H2pT"]    = std::make_shared<dumpBranch>("VHH_H2_pT", 'F');
            variables["H2eta"]   = std::make_shared<dumpBranch>("VHH_H2_eta", 'F');
            variables["HHm"]     = std::make_shared<dumpBranch>("VHH_HH_m", 'F');
            variables["HHE"]     = std::make_shared<dumpBranch>("VHH_HH_e", 'F');
            variables["HHpT"]    = std::make_shared<dumpBranch>("VHH_HH_pT", 'F');
            variables["HHeta"]   = std::make_shared<dumpBranch>("VHH_HH_eta", 'F');
            variables["HHdeta"]  = std::make_shared<dumpBranch>("VHH_HH_deta", 'F');
            variables["HHdphi"]  = std::make_shared<dumpBranch>("VHH_HH_dphi", 'F');
            variables["HHdR"]    = std::make_shared<dumpBranch>("VHH_HH_dR", 'F');
            variables["H2H1rpT"] = std::make_shared<dumpBranch>("VHH_H2H1_pt_ratio", 'F');
            variables["VH1phi"]  = std::make_shared<dumpBranch>("VHH_V_H1_dPhi", 'F');
            variables["VH2phi"]  = std::make_shared<dumpBranch>("VHH_V_H2_dPhi", 'F');
            for (const auto & [key, value] : variables)
            {
                rootTree->Branch(value->name.c_str(), value->value, value->leafname());
            }
        }
    }
    void dumpRoot::fill()
    {
        if(rootTree)
        {
            rootTree->Fill();
        }
    }
    void dumpRoot::close()
    {
        if(rootFile)
        {
            rootFile->Write();
            rootFile->Close();
        }
    }
}

