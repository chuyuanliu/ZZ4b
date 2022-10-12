// -*- C++ -*-
#if !defined(viewHists_H)
#define viewHists_H

#include <iostream>
#include <TH1F.h>
#include <TH2F.h>
#include "PhysicsTools/FWLite/interface/TFileService.h"
#include "ZZ4b/nTupleAnalysis/interface/eventData.h"
#include "ZZ4b/nTupleAnalysis/interface/eventView.h"
#include "nTupleAnalysis/baseClasses/interface/fourVectorHists.h"
#include "nTupleAnalysis/baseClasses/interface/jetHists.h"
#include "nTupleAnalysis/baseClasses/interface/muonHists.h"
#include "nTupleAnalysis/baseClasses/interface/elecHists.h"
#include "nTupleAnalysis/baseClasses/interface/dijetHists.h"
#include "nTupleAnalysis/baseClasses/interface/trijetHists.h"
#include "nTupleAnalysis/baseClasses/interface/trigHists.h"
#include "nTupleAnalysis/baseClasses/interface/systHists.h"
#include "ZZ4b/nTupleAnalysis/interface/weightStudyHists.h"
#include "ZZ4b/nTupleAnalysis/interface/ratioSystHistsProducer.h"

namespace nTupleAnalysis {

  class viewHists {
  public:
    TFileDirectory dir;
    bool debug;
    
    // Object Level
    TH1F*     nAllJets;
    TH1F*     nAllNotCanJets;
    TH1F*     st;
    TH1F*     nSelJets;
    TH1F*     nSelJets_noBTagSF;
    TH1F*     nSelJets_lowSt;
    TH1F*     nSelJets_midSt;
    TH1F*     nSelJets_highSt;
    TH1F*     nSelJetsUnweighted;
    TH1F*     nSelJetsUnweighted_lowSt;
    TH1F*     nSelJetsUnweighted_midSt;
    TH1F*     nSelJetsUnweighted_highSt;
    TH1F*     nTagJets;
    TH1F*     nTagJetsUnweighted;
    TH1F*     nPSTJets;
    TH1F*     nPSTJets_lowSt;
    TH1F*     nPSTJets_midSt;
    TH1F*     nPSTJets_highSt;
    TH1F*     nPSTJetsUnweighted;
    TH1F*     nCanJets;
    //jetHists*  allJets;
    jetHists*  selJets;
    jetHists*  tagJets;
    jetHists*  canJets;
    jetHists*  canJet0;
    jetHists*  canJet1;
    jetHists*  canJet2;
    jetHists*  canJet3;
    jetHists*  othJets;
    jetHists*  allNotCanJets;
    TH1F* aveAbsEta;
    TH1F* aveAbsEtaOth;
    TH1F* stNotCan;
    //VHH
    TH1F* nTruVJets;
    jetHists* truVJets;
    jetHists* canVJets;
    jetHists* canVJet0;
    jetHists* canVJet1;
    TH1F* nCanHTruVJets;
    TH1F* nCanVDijets;
    dijetHists* canVDijets;
    TH1F* kl_BDT;

    TH1F* puIdSF;
    TH1F* SvB_MA_VHH_ps;
    TH1F* SvB_MA_VHH_ps_BDT_kVV;
    TH1F* SvB_MA_VHH_ps_BDT_kl;
    sTH1F sSvB_MA_VHH_ps;
    sTH1F sSvB_MA_VHH_ps_BDT_kVV;
    sTH1F sSvB_MA_VHH_ps_BDT_kl;
    systHists* SvB_MA_VHH_ps_bTagSysts =NULL;
    systHists* SvB_MA_VHH_ps_BDT_kVV_bTagSysts = NULL;
    systHists* SvB_MA_VHH_ps_BDT_kl_bTagSysts = NULL;
    systHists* SvB_MA_VHH_ps_puIdSysts =NULL;
    systHists* SvB_MA_VHH_ps_BDT_kVV_puIdSysts = NULL;
    systHists* SvB_MA_VHH_ps_BDT_kl_puIdSysts = NULL;
    systHists* SvB_MA_VHH_ps_zhhNNLOSysts =NULL;
    systHists* SvB_MA_VHH_ps_BDT_kVV_zhhNNLOSysts = NULL;
    systHists* SvB_MA_VHH_ps_BDT_kl_zhhNNLOSysts = NULL;

    TH1F* SvB_MA_VHH_ps_ONNX;
    TH1F* SvB_MA_VHH_ps_BDT_kVV_ONNX;
    TH1F* SvB_MA_VHH_ps_BDT_kl_ONNX;
    systHists* SvB_MA_VHH_ps_ONNX_bTagSysts =NULL;
    systHists* SvB_MA_VHH_ps_BDT_kVV_ONNX_bTagSysts = NULL;
    systHists* SvB_MA_VHH_ps_BDT_kl_ONNX_bTagSysts = NULL; 
    //
    trigHists*  allTrigJets = NULL;

    TH1F* nAllMuons;
    TH1F* nIsoMed25Muons;
    TH1F* nIsoMed40Muons;
    muonHists* allMuons;
    muonHists* muons_isoMed25;
    muonHists* muons_isoMed40;

    TH1F* nAllElecs;
    TH1F* nIsoMed25Elecs;
    TH1F* nIsoMed40Elecs;
    elecHists* allElecs;
    elecHists* elecs_isoMed25;
    elecHists* elecs_isoMed40;


    dijetHists* lead;
    dijetHists* subl;
    TH2F* lead_m_vs_subl_m;

    dijetHists* leadSt;
    dijetHists* sublSt;
    TH2F* leadSt_m_vs_sublSt_m;

    TH2F* m4j_vs_leadSt_dR;
    TH2F* m4j_vs_sublSt_dR;

    dijetHists* leadM;
    dijetHists* sublM;
    TH2F* leadM_m_vs_sublM_m;

    dijetHists* close;
    dijetHists* other;
    TH2F* close_m_vs_other_m;

    // PU jet ID SF

    TH2F* allBJets = NULL;
    TH2F* allNotBJets = NULL;
    TH2F* allBJetsPassPuId = NULL;
    TH2F* allNotBJetsPassPuId = NULL;

    TH2F* allPUBJets = NULL;
    TH2F* allPUBJetsPassPuId = NULL;
    TH2F* allPUNotBJets = NULL;
    TH2F* allPUNotBJetsPassPuId = NULL;

    // Event Level
    TH1F* nPVs;
    TH1F* nPVsGood;    
    fourVectorHists* v4j;
    TH1F* s4j;
    TH1F* r4j;
    // TH1F* m123;
    // TH1F* m023;
    // TH1F* m013;
    // TH1F* m012;
    TH1F* dBB;
    TH1F* dEtaBB;
    TH1F* dRBB;
    TH1F* xZZ;
    TH1F* mZZ;
    TH1F* xZH;
    TH1F* mZH;
    TH1F* xHH;
    TH1F* mHH;

    TH1F* hT;
    TH1F* hT30;
    TH1F* L1hT;
    TH1F* L1hT30;
    TH1F* HLThT;
    TH1F* HLThT30;

    TH1F* xWt0;
    TH1F* xWt1;
    //TH1F* xWt2;
    TH1F* xWt;
    trijetHists* t0;
    trijetHists* t1;
    //trijetHists* t2;
    trijetHists* t;

    TH1F* FvT;
    TH1F* FvTUnweighted;
    TH1F* FvT_pd4;
    TH1F* FvT_pd3;
    TH1F* FvT_pt4;
    TH1F* FvT_pt3;
    TH1F* FvT_pm4;
    TH1F* FvT_pm3;
    TH1F* FvT_pt;
    TH1F* FvT_std;
    TH1F* FvT_ferr;
    TH1F* SvB_ps;
    TH1F* SvB_pwhh;
    TH1F* SvB_pzhh;
    TH1F* SvB_ptt;
    TH1F* SvB_ps_zhh;
    TH1F* SvB_ps_whh;
    systHists* SvB_ps_bTagSysts = NULL;
    TH1F* SvB_MA_ps;
    TH1F* SvB_MA_pwhh;
    TH1F* SvB_MA_pzhh;
    TH1F* SvB_MA_ptt;
    TH1F* SvB_MA_ps_zhh;
    TH1F* SvB_MA_ps_whh;
    systHists* SvB_MA_ps_bTagSysts = NULL;

    //Simplified template cross section binning https://cds.cern.ch/record/2669925/files/1906.02754.pdf

    TH1F* FvT_q_score;
    TH1F* FvT_q_score_dR_min;
    TH1F* FvT_q_score_SvB_q_score_max;
    TH1F* SvB_q_score;
    TH1F* SvB_q_score_FvT_q_score_max;
    TH1F* SvB_MA_q_score;

    TH1F* FvT_SvB_q_score_max_same;

    TH2F* m4j_vs_nViews_eq;
    TH2F* m4j_vs_nViews_00;
    TH2F* m4j_vs_nViews_01;
    TH2F* m4j_vs_nViews_02;
    TH2F* m4j_vs_nViews_10;
    TH2F* m4j_vs_nViews_11;
    TH2F* m4j_vs_nViews_12;
    
    TH1F* truthM4b;
    TH2F* truthM4b_vs_mZH;
    TH1F* nTrueBJets;

    weightStudyHists* weightStudy_v0v1  = NULL;
    weightStudyHists* weightStudy_v0v9  = NULL;
    weightStudyHists* weightStudy_os012 = NULL;
    weightStudyHists* weightStudy_e20   = NULL;

    sRSyst triggerSyst = nullptr;
    sRSyst triggerSyst_kVV = nullptr;
    sRSyst triggerSyst_kl = nullptr;

    viewHists(std::string, fwlite::TFileService&, bool isMC = false, bool _debug = false, eventData* event = NULL, std::string histDetailLevel="");
    void Fill(eventData*, std::shared_ptr<eventView>&);//, int nViews=-1, int nViews_10=-1, int nViews_11=-1, int nViews_12=-1);
    ~viewHists(); 

  };

}
#endif // viewHists_H
