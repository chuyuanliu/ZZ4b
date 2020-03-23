// -*- C++ -*-
#if !defined(cutflowHists_H)
#define cutflowHists_H

#include <iostream>
#include <TH1F.h>
#include <TH2F.h>
#include "PhysicsTools/FWLite/interface/TFileService.h"
#include "ZZ4b/nTupleAnalysis/interface/eventData.h"

namespace nTupleAnalysis {

  class cutflowHists {
  public:
    TFileDirectory dir;
    
    TH1F* unitWeight;
    TH1F* weighted;

    TH1F* Mu1_NoPt;
    TH1F* Mu1_5GeV;
    TH1F* Mu2_NoPt;
    TH1F* Mu2_5GeV;

    TH1F* MC;

    TH1F* muonTrigs;
    TH1F* muonTrigsHiMass;
    TH1F* muonTrigsLoMass;

    TH1F* muTrigs_noMC;
    TH1F* muTrigs_HiMass_noMC;
    TH1F* muTrigs_LoMass_noMC;

    TH1F* muTrigs_noMC_sip;
    TH1F* muTrigs_HiMass_noMC_sip;
    TH1F* muTrigs_LoMass_noMC_sip;

    TH1F* muonPt;
    TH1F* Muon_ip3d;
    TH1F* Muon_dxy;
    TH1F* Muon_dxyErr;
    TH1F* Muon_sip3d;
    TH1F* Mu_pt_7;
    TH1F* Mu_ip3d_7;
    TH1F* Mu_dxy_7;
    TH1F* Mu_dxyErr_7;
    TH1F* Mu_sip3d_7;
    TH1F* Mu_pt_8;
    TH1F* Mu_ip3d_8;
    TH1F* Mu_dxy_8;
    TH1F* Mu_dxyErr_8;
    TH1F* Mu_sip3d_8;
    TH1F* Mu_pt_9;
    TH1F* Mu_ip3d_9;
    TH1F* Mu_dxy_9;
    TH1F* Mu_dxyErr_9;
    TH1F* Mu_sip3d_9;
    TH1F* Mu_pt_12;
    TH1F* Mu_ip3d_12;
    TH1F* Mu_dxy_12;
    TH1F* Mu_dxyErr_12;
    TH1F* Mu_sip3d_12;
    TH1F* HLT_Mu12_IP6_ip3d;
    TH1F* HLT_Mu12_IP6_dxy;
    TH1F* HLT_Mu12_IP6_dxyErr;
    TH1F* HLT_Mu12_IP6_sip3d;
    TH1F* HLT_Mu9_IP6_ip3d;
    TH1F* HLT_Mu9_IP6_dxy;
    TH1F* HLT_Mu9_IP6_dxyErr;
    TH1F* HLT_Mu9_IP6_sip3d;
    TH1F* HLT_Mu9_IP5_ip3d;
    TH1F* HLT_Mu9_IP5_dxy;
    TH1F* HLT_Mu9_IP5_dxyErr;
    TH1F* HLT_Mu9_IP5_sip3d;
    TH1F* HLT_Mu9_IP4_ip3d;
    TH1F* HLT_Mu9_IP4_dxy;
    TH1F* HLT_Mu9_IP4_dxyErr;
    TH1F* HLT_Mu9_IP4_sip3d;
    TH1F* HLT_Mu8_IP6_ip3d;
    TH1F* HLT_Mu8_IP6_dxy;
    TH1F* HLT_Mu8_IP6_dxyErr;
    TH1F* HLT_Mu8_IP6_sip3d;
    TH1F* HLT_Mu8_IP5_ip3d;
    TH1F* HLT_Mu8_IP5_dxy;
    TH1F* HLT_Mu8_IP5_dxyErr;
    TH1F* HLT_Mu8_IP5_sip3d;
    TH1F* HLT_Mu8_IP3_ip3d;
    TH1F* HLT_Mu8_IP3_dxy;
    TH1F* HLT_Mu8_IP3_dxyErr;
    TH1F* HLT_Mu8_IP3_sip3d;
    TH1F* HLT_Mu7_IP4_ip3d;
    TH1F* HLT_Mu7_IP4_dxy;
    TH1F* HLT_Mu7_IP4_dxyErr;
    TH1F* HLT_Mu7_IP4_sip3d;

    TH1F* sip3d_Mu12_IP6;
    TH1F* sip3d_Mu9_IP6;
    TH1F* sip3d_Mu9_IP5;
    TH1F* sip3d_Mu9_IP4;
    TH1F* sip3d_Mu8_IP6;
    TH1F* sip3d_Mu8_IP5;
    TH1F* sip3d_Mu8_IP3;
    TH1F* sip3d_Mu7_IP4;

    TH2F* truthM4b = NULL;

    cutflowHists(std::string, fwlite::TFileService&, bool);
    void BasicFill(const std::string&, eventData*);
    void BasicFill(const std::string&, eventData*, float weight);
    void Fill(const std::string&, eventData*);

    void labelsDeflate();

    void AddCut(std::string cut);
    
    ~cutflowHists(); 

  };

}
#endif // cutflowHists_H
