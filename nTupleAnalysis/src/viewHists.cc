#include "ZZ4b/nTupleAnalysis/interface/viewHists.h"
#include "nTupleAnalysis/baseClasses/interface/helpers.h"

using namespace nTupleAnalysis;

viewHists::viewHists(std::string name, fwlite::TFileService& fs, bool isMC, bool _debug, eventData* event, std::string histDetailLevel) {
  if(_debug) std::cout << "viewHists::viewHists(std::string name, fwlite::TFileService& fs, bool isMC, bool _debug, eventData* event, std::string histDetailLevel)" << std::endl;
  dir = fs.mkdir(name);
  debug = _debug;

  //
  // Object Level
  //
  nAllJets = dir.make<TH1F>("nAllJets", (name+"/nAllJets; Number of Jets (pt>20); Entries").c_str(),  16,-0.5,15.5);
  nAllNotCanJets = dir.make<TH1F>("nAllNotCanJets", (name+"/nAllNotCanJets; Number of Jets excluding boson candidate jets (pt>20); Entries").c_str(),  16,-0.5,15.5);
  nSelJets = dir.make<TH1F>("nSelJets", (name+"/nSelJets; Number of Selected Jets; Entries").c_str(),  16,-0.5,15.5);
  nSelJets_noBTagSF = dir.make<TH1F>("nSelJets_noBTagSF", (name+"/nSelJets_noBTagSF; Number of Selected Jets; Entries").c_str(),  16,-0.5,15.5);
  nSelJets_lowSt = dir.make<TH1F>("nSelJets_lowSt", (name+"/nSelJets_lowSt; Number of Selected Jets; Entries").c_str(),  16,-0.5,15.5);
  nSelJets_midSt = dir.make<TH1F>("nSelJets_midSt", (name+"/nSelJets_midSt; Number of Selected Jets; Entries").c_str(),  16,-0.5,15.5);
  nSelJets_highSt = dir.make<TH1F>("nSelJets_highSt", (name+"/nSelJets_highSt; Number of Selected Jets; Entries").c_str(),  16,-0.5,15.5);
  nSelJetsUnweighted = dir.make<TH1F>("nSelJetsUnweighted", (name+"/nSelJetsUnweighted; Number of Selected Jets (Unweighted); Entries").c_str(),  16,-0.5,15.5);
  nSelJetsUnweighted_lowSt = dir.make<TH1F>("nSelJetsUnweighted_lowSt", (name+"/nSelJetsUnweighted_lowSt; Number of Selected (Unweighted) Jets; Entries").c_str(),  16,-0.5,15.5);
  nSelJetsUnweighted_midSt = dir.make<TH1F>("nSelJetsUnweighted_midSt", (name+"/nSelJetsUnweighted_midSt; Number of Selected (Unweighted) Jets; Entries").c_str(),  16,-0.5,15.5);
  nSelJetsUnweighted_highSt = dir.make<TH1F>("nSelJetsUnweighted_highSt", (name+"/nSelJetsUnweighted_highSt; Number of Selected (Unweighted) Jets; Entries").c_str(),  16,-0.5,15.5);
  nTagJets = dir.make<TH1F>("nTagJets", (name+"/nTagJets; Number of Tagged Jets; Entries").c_str(),  16,-0.5,15.5);
  nTagJetsUnweighted = dir.make<TH1F>("nTagJetsUnweighted", (name+"/nTagJets; Number of Tagged Jets; Entries").c_str(),  16,-0.5,15.5);
  nPSTJets = dir.make<TH1F>("nPSTJets", (name+"/nPSTJets; Number of Tagged + Pseudo-Tagged Jets; Entries").c_str(),  16,-0.5,15.5);
  nPSTJets_lowSt = dir.make<TH1F>("nPSTJets_lowSt", (name+"/nPSTJets_lowSt; Number of Tagged + Pseudo-Tagged Jets; Entries").c_str(),  16,-0.5,15.5);
  nPSTJets_midSt = dir.make<TH1F>("nPSTJets_midSt", (name+"/nPSTJets_midSt; Number of Tagged + Pseudo-Tagged Jets; Entries").c_str(),  16,-0.5,15.5);
  nPSTJets_highSt = dir.make<TH1F>("nPSTJets_highSt", (name+"/nPSTJets_highSt; Number of Tagged + Pseudo-Tagged Jets; Entries").c_str(),  16,-0.5,15.5);
  nPSTJetsUnweighted = dir.make<TH1F>("nPSTJetsUnweighted", (name+"/nPSTJetsUnweighted; Number of Tagged + Pseudo-Tagged (Unweighted) Jets; Entries").c_str(),  16,-0.5,15.5);
  nCanJets = dir.make<TH1F>("nCanJets", (name+"/nCanJets; Number of Boson Candidate Jets; Entries").c_str(),  16,-0.5,15.5);
  //allJets = new jetHists(name+"/allJets", fs, "All Jets");
  allNotCanJets = new jetHists(name+"/allNotCanJets", fs, "All Jets Excluding Boson Candidate Jets");
  selJets = new jetHists(name+"/selJets", fs, "Selected Jets", "", debug);
  tagJets = new jetHists(name+"/tagJets", fs, "Tagged Jets");
  canJets = new jetHists(name+"/canJets", fs, "Higgs Boson Candidate Jets");
  canJet0 = new jetHists(name+"/canJet0", fs, "Higgs Boson Candidate Jet_{0}");
  canJet1 = new jetHists(name+"/canJet1", fs, "Higgs Boson Candidate Jet_{1}");
  canJet2 = new jetHists(name+"/canJet2", fs, "Higgs Boson Candidate Jet_{2}");
  canJet3 = new jetHists(name+"/canJet3", fs, "Higgs Boson Candidate Jet_{3}");
  othJets = new jetHists(name+"/othJets", fs, "Other Selected Jets");
  //VHH
  nTruVJets = dir.make<TH1F>("nTruVJets", (name+"/nTruVJets; Number of Truth Matched Vector Boson Jets in Other Jets; Entries").c_str(), 16,-0.5,15.5);
  truVJets = new jetHists(name+"/truVJets", fs, "Truth Matched Vector Boson Jets in Other Jets");
  nCanHTruVJets = dir.make<TH1F>("nCanHTruVJets", (name+"/nCanHTruVJets; Number of Truth Matched Vector Boson Jets in Higgs Candidate Jets; Entries").c_str(), 16,-0.5,15.5);
  nCanVDijets =dir.make<TH1F>("nCanVDijets", (name+"/nCanVDijets; Number of Vector Boson Candidate Dijets; Entries").c_str(), 16,-0.5,15.5);
  canVJets = new jetHists(name+"/canVJets", fs, "Vector Boson Candidate Jets");
  canVJet0 = new jetHists(name+"/canVJet0", fs, "Vector Boson Candidate Jet_{0}");
  canVJet1 = new jetHists(name+"/canVJet1", fs, "Vector Boson Candidate Jet_{1}"); 
  canVDijets   = new dijetHists(name+"/canVDijets",   fs,    "Vector Boson Candidate Dijets");
  //
  aveAbsEta = dir.make<TH1F>("aveAbsEta", (name+"/aveAbsEta; <|#eta|>; Entries").c_str(), 25, 0 , 2.5);
  aveAbsEtaOth = dir.make<TH1F>("aveAbsEtaOth", (name+"/aveAbsEtaOth; Other Jets <|#eta|>; Entries").c_str(), 27, -0.2, 2.5);
  //allTrigJets = new trigHists(name+"/allTrigJets", fs, "All Trig Jets");
    

  nAllMuons = dir.make<TH1F>("nAllMuons", (name+"/nAllMuons; Number of Muons (no selection); Entries").c_str(),  6,-0.5,5.5);
  nIsoMed25Muons = dir.make<TH1F>("nIsoMed25Muons", (name+"/nIsoMed25Muons; Number of Prompt Muons; Entries").c_str(),  6,-0.5,5.5);
  nIsoMed40Muons = dir.make<TH1F>("nIsoMed40Muons", (name+"/nIsoMed40Muons; Number of Prompt Muons; Entries").c_str(),  6,-0.5,5.5);
  allMuons        = new muonHists(name+"/allMuons", fs, "All Muons");
  muons_isoMed25  = new muonHists(name+"/muon_isoMed25", fs, "iso Medium 25 Muons");
  muons_isoMed40  = new muonHists(name+"/muon_isoMed40", fs, "iso Medium 40 Muons");

  nAllElecs = dir.make<TH1F>("nAllElecs", (name+"/nAllElecs; Number of Elecs (no selection); Entries").c_str(),  16,-0.5,15.5);
  nIsoMed25Elecs = dir.make<TH1F>("nIsoMed25Elecs", (name+"/nIsoMed25Elecs; Number of Prompt Elecs; Entries").c_str(),  6,-0.5,5.5);
  nIsoMed40Elecs = dir.make<TH1F>("nIsoMed40Elecs", (name+"/nIsoMed40Elecs; Number of Prompt Elecs; Entries").c_str(),  6,-0.5,5.5);
  allElecs        = new elecHists(name+"/allElecs", fs, "All Elecs");
  elecs_isoMed25  = new elecHists(name+"/elec_isoMed25", fs, "iso Medium 25 Elecs");
  elecs_isoMed40  = new elecHists(name+"/elec_isoMed40", fs, "iso Medium 40 Elecs");


  lead   = new dijetHists(name+"/lead",   fs,    "Leading p_{T} boson candidate");
  subl   = new dijetHists(name+"/subl",   fs, "Subleading p_{T} boson candidate");
  lead_m_vs_subl_m = dir.make<TH2F>("lead_m_vs_subl_m", (name+"/lead_m_vs_subl_m; p_{T} leading boson candidate Mass [GeV]; p_{T} subleading boson candidate Mass [GeV]; Entries").c_str(), 50,0,250, 50,0,250);

  leadSt = new dijetHists(name+"/leadSt", fs,    "Leading S_{T} boson candidate");
  sublSt = new dijetHists(name+"/sublSt", fs, "Subleading S_{T} boson candidate");
  leadSt_m_vs_sublSt_m = dir.make<TH2F>("leadSt_m_vs_sublSt_m", (name+"/leadSt_m_vs_sublSt_m; S_{T} leading boson candidate Mass [GeV]; S_{T} subleading boson candidate Mass [GeV]; Entries").c_str(), 50,0,250, 50,0,250);


  m4j_vs_leadSt_dR = dir.make<TH2F>("m4j_vs_leadSt_dR", (name+"/m4j_vs_leadSt_dR; m_{4j} [GeV]; S_{T} leading Higgs candidate #DeltaR(j,j); Entries").c_str(), 40,100,1200, 25,0,5);
  m4j_vs_sublSt_dR = dir.make<TH2F>("m4j_vs_sublSt_dR", (name+"/m4j_vs_sublSt_dR; m_{4j} [GeV]; S_{T} subleading Higgs candidate #DeltaR(j,j); Entries").c_str(), 40,100,1200, 25,0,5);

  leadM  = new dijetHists(name+"/leadM",  fs,    "Leading mass boson candidate");
  sublM  = new dijetHists(name+"/sublM",  fs, "Subleading mass boson candidate");
  leadM_m_vs_sublM_m = dir.make<TH2F>("leadM_m_vs_sublM_m", (name+"/leadM_m_vs_sublM_m; mass leading boson candidate Mass [GeV]; mass subleading boson candidate Mass [GeV]; Entries").c_str(), 50,0,250, 50,0,250);

  close  = new dijetHists(name+"/close",  fs,               "Minimum #DeltaR(j,j) Dijet");
  other  = new dijetHists(name+"/other",  fs, "Complement of Minimum #DeltaR(j,j) Dijet");
  close_m_vs_other_m = dir.make<TH2F>("close_m_vs_other_m", (name+"/close_m_vs_other_m; Minimum #DeltaR(j,j) Dijet Mass [GeV]; Complement of Minimum #DeltaR(j,j) Dijet Mass [GeV]; Entries").c_str(), 50,0,250, 50,0,250);
    
  // PU jet ID SF
  if(event){
    if(event->calcPuIdSF){
      allBJets = dir.make<TH2F>("allBJets", (name+"/allBJets; p_{T}; #eta; Entries").c_str(), 6, 20, 50, 10, -2.5, 2.5);
      allNotBJets = dir.make<TH2F>("allNotBJets", (name+"/allNotBJets; p_{T}; #eta; Entries").c_str(), 6, 20, 50, 10, -2.5, 2.5);
      allBJetsPassPuId = dir.make<TH2F>("allBJetsPassPuId", (name+"/allBJetsPassPuId; p_{T}; #eta; Entries").c_str(), 6, 20, 50, 10, -2.5, 2.5);
      allNotBJetsPassPuId = dir.make<TH2F>("allNotBJetsPassPuId", (name+"/allNotBJetsPassPuId; p_{T}; #eta; Entries").c_str(), 6, 20, 50, 10, -2.5, 2.5);

      allPUBJets = dir.make<TH2F>("allPUBJets", (name+"/allPUBJets; p_{T}; #eta; Entries").c_str(), 6, 20, 50, 10, -2.5, 2.5);
      allPUBJetsPassPuId = dir.make<TH2F>("allPUBJetsPassPuId", (name+"/allPUBJetsPassPuId; p_{T}; #eta; Entries").c_str(), 6, 20, 50, 10, -2.5, 2.5);
      allPUNotBJets = dir.make<TH2F>("allPUNotBJets", (name+"/allPUNotBJets; p_{T}; #eta; Entries").c_str(), 6, 20, 50, 10, -2.5, 2.5);
      allPUNotBJetsPassPuId = dir.make<TH2F>("allPUNotBJetsPassPuId", (name+"/allPUNotBJetsPassPuId; p_{T}; #eta; Entries").c_str(), 6, 20, 50, 10, -2.5, 2.5);
    }
  }

  //
  // Event  Level
  //
  nPVs = dir.make<TH1F>("nPVs", (name+"/nPVs; Number of Primary Vertices; Entries").c_str(), 101, -0.5, 100.5);
  nPVsGood = dir.make<TH1F>("nPVsGood", (name+"/nPVs; Number of Good (!isFake && ndof > 4 && abs(z) <= 24 && position.Rho <= 2) Primary Vertices; Entries").c_str(), 101, -0.5, 100.5);
  st = dir.make<TH1F>("st", (name+"/st; Scalar sum of jet p_{T}'s [GeV]; Entries").c_str(), 130, 200, 1500);
  stNotCan = dir.make<TH1F>("stNotCan", (name+"/stNotCan; Scalar sum all other jet p_{T}'s [GeV]; Entries").c_str(), 150, 0, 1500);
  v4j = new fourVectorHists(name+"/v4j", fs, "4j");
  s4j = dir.make<TH1F>("s4j", (name+"/s4j; Scalar sum of boson candidate jet p_{T}'s [GeV]; Entries").c_str(), 90, 100, 1000);
  r4j = dir.make<TH1F>("r4j", (name+"/r4j; Quadjet system p_{T} / s_{T}; Entries").c_str(), 50, 0, 1);
  // m123 = dir.make<TH1F>("m123", (name+"/m123; m_{1,2,3}; Entries").c_str(), 100, 0, 1000);
  // m023 = dir.make<TH1F>("m023", (name+"/m023; m_{0,2,3}; Entries").c_str(), 100, 0, 1000);
  // m013 = dir.make<TH1F>("m013", (name+"/m013; m_{0,1,3}; Entries").c_str(), 100, 0, 1000);
  // m012 = dir.make<TH1F>("m012", (name+"/m012; m_{0,1,2}; Entries").c_str(), 100, 0, 1000);
  dBB = dir.make<TH1F>("dBB", (name+"/dBB; D_{BB}; Entries").c_str(), 40, 0, 200);
  dEtaBB = dir.make<TH1F>("dEtaBB", (name+"/dEtaBB; #Delta#eta_{BB}; Entries").c_str(), 100, -5, 5);
  dRBB = dir.make<TH1F>("dRBB", (name+"/dRBB; #Delta#R_{BB}; Entries").c_str(), 50, 0, 5);

  xZZ = dir.make<TH1F>("xZZ", (name+"/xZZ; X_{ZZ}; Entries").c_str(), 100, 0, 10);
  Double_t bins_mZZ[] = {100, 182, 200, 220, 242, 266, 292, 321, 353, 388, 426, 468, 514, 565, 621, 683, 751, 826, 908, 998, 1097, 1206, 1326, 1500};
  mZZ = dir.make<TH1F>("mZZ", (name+"/mZZ; m_{ZZ} [GeV]; Entries").c_str(), 23, bins_mZZ);

  xZH = dir.make<TH1F>("xZH", (name+"/xZH; X_{ZH}; Entries").c_str(), 100, 0, 10);  
  Double_t bins_mZH[] = {100, 216, 237, 260, 286, 314, 345, 379, 416, 457, 502, 552, 607, 667, 733, 806, 886, 974, 1071, 1178, 1295, 1500};
  mZH = dir.make<TH1F>("mZH", (name+"/mZH; m_{ZH} [GeV]; Entries").c_str(), 21, bins_mZH);

  xWt0 = dir.make<TH1F>("xWt0", (name+"/xWt0; X_{Wt,0}; Entries").c_str(), 60, 0, 12);
  xWt1 = dir.make<TH1F>("xWt1", (name+"/xWt1; X_{Wt,1}; Entries").c_str(), 60, 0, 12);
  //xWt2 = dir.make<TH1F>("xWt2", (name+"/xWt2; X_{Wt,2}; Entries").c_str(), 60, 0, 12);
  xWt  = dir.make<TH1F>("xWt",  (name+"/xWt;  X_{Wt};   Entries").c_str(), 60, 0, 12);
  t0 = new trijetHists(name+"/t0",  fs, "Top Candidate (#geq0 non-candidate jets)");
  t1 = new trijetHists(name+"/t1",  fs, "Top Candidate (#geq1 non-candidate jets)");
  //t2 = new trijetHists(name+"/t2",  fs, "Top Candidate (#geq2 non-candidate jets)");
  t = new trijetHists(name+"/t",  fs, "Top Candidate");

  FvT = dir.make<TH1F>("FvT", (name+"/FvT; Kinematic Reweight; Entries").c_str(), 100, 0, 5);
  FvTUnweighted = dir.make<TH1F>("FvTUnweighted", (name+"/FvTUnweighted; Kinematic Reweight; Entries").c_str(), 100, 0, 5);
  // FvT_pd4 = dir.make<TH1F>("FvT_pd4", (name+"/FvT_pd4; FvT Regressed P(Four-tag Data) ; Entries").c_str(), 100, 0, 1);
  // FvT_pd3 = dir.make<TH1F>("FvT_pd3", (name+"/FvT_pd3; FvT Regressed P(Three-tag Data) ; Entries").c_str(), 100, 0, 1);
  // FvT_pt4 = dir.make<TH1F>("FvT_pt4", (name+"/FvT_pt4; FvT Regressed P(Four-tag t#bar{t}) ; Entries").c_str(), 100, 0, 1);
  // FvT_pt3 = dir.make<TH1F>("FvT_pt3", (name+"/FvT_pt3; FvT Regressed P(Three-tag t#bar{t}) ; Entries").c_str(), 100, 0, 1);
  // FvT_pm4 = dir.make<TH1F>("FvT_pm4", (name+"/FvT_pm4; FvT Regressed P(Four-tag Multijet) ; Entries").c_str(), 100, 0, 1);
  // FvT_pm3 = dir.make<TH1F>("FvT_pm3", (name+"/FvT_pm3; FvT Regressed P(Three-tag Multijet) ; Entries").c_str(), 100, 0, 1);
  // FvT_pt  = dir.make<TH1F>("FvT_pt",  (name+"/FvT_pt;  FvT Regressed P(t#bar{t}) ; Entries").c_str(), 100, 0, 1);
  // SvB_ps  = dir.make<TH1F>("SvB_ps",  (name+"/SvB_ps;  SvB Regressed P(WHH)+P(ZHH); Entries").c_str(), 100, 0, 1);
  // FvT_std = dir.make<TH1F>("FvT_std",  (name+"/FvT_pt;  FvT Standard Deviation ; Entries").c_str(), 100, 0, 5);
  // FvT_ferr = dir.make<TH1F>("FvT_ferr",  (name+"/FvT_ferr;  FvT std/FvT ; Entries").c_str(), 100, 0, 5);
  // if(event){
  //   SvB_ps_bTagSysts = new systHists(SvB_ps, event->treeJets->m_btagVariations);
  // }
  // SvB_pwhh = dir.make<TH1F>("SvB_pwhh", (name+"/SvB_pwhh; SvB Regressed P(WHH); Entries").c_str(), 100, 0, 1);
  // SvB_pzhh = dir.make<TH1F>("SvB_pzhh", (name+"/SvB_pzhh; SvB Regressed P(ZHH); Entries").c_str(), 100, 0, 1);
  // SvB_ptt = dir.make<TH1F>("SvB_ptt", (name+"/SvB_ptt; SvB Regressed P(t#bar{t}); Entries").c_str(), 100, 0, 1);
  // SvB_ps_zhh = dir.make<TH1F>("SvB_ps_zhh",  (name+"/SvB_ps_zhh;  SvB Regressed P(WHH)+P(ZHH), P(ZHH)$ #geq P(WHH); Entries").c_str(), 100, 0, 1);
  // SvB_ps_whh = dir.make<TH1F>("SvB_ps_whh",  (name+"/SvB_ps_whh;  SvB Regressed P(WHH)+P(ZHH), P(WHH) > P(ZHH); Entries").c_str(), 100, 0, 1);

  // SvB_MA_ps  = dir.make<TH1F>("SvB_MA_ps",  (name+"/SvB_MA_ps;  SvB_MA Regressed P(WHH)+P(ZHH); Entries").c_str(), 100, 0, 1);
  // if(event){
  //   SvB_MA_ps_bTagSysts = new systHists(SvB_MA_ps, event->treeJets->m_btagVariations);
  // }
  // SvB_MA_pwhh = dir.make<TH1F>("SvB_MA_pwhh", (name+"/SvB_MA_pwhh; SvB_MA Regressed P(WHH); Entries").c_str(), 100, 0, 1);
  // SvB_MA_pzhh = dir.make<TH1F>("SvB_MA_pzhh", (name+"/SvB_MA_pzhh; SvB_MA Regressed P(ZHH); Entries").c_str(), 100, 0, 1);
  // SvB_MA_ptt = dir.make<TH1F>("SvB_MA_ptt", (name+"/SvB_MA_ptt; SvB_MA Regressed P(t#bar{t}); Entries").c_str(), 100, 0, 1);
  // SvB_MA_ps_zhh = dir.make<TH1F>("SvB_MA_ps_zhh",  (name+"/SvB_MA_ps_zhh;  SvB_MA Regressed P(WHH)+P(ZHH), P(ZHH)$ #geq P(WHH); Entries").c_str(), 100, 0, 1);
  // SvB_MA_ps_whh = dir.make<TH1F>("SvB_MA_ps_whh",  (name+"/SvB_MA_ps_whh;  SvB_MA Regressed P(WHH)+P(ZHH), P(WHH) > P(ZHH); Entries").c_str(), 100, 0, 1);

  puIdSF = dir.make<TH1F>("puIdSF",  (name+"/puIdSF;  PU Jet ID SF; Entries").c_str(), 60, 0.7, 1.3);
  SvB_MA_VHH_ps  = dir.make<TH1F>("SvB_MA_VHH_ps",  (name+"/SvB_MA_VHH_ps;  SvB_MA Regressed P(VHH); Entries").c_str(), 100, 0, 1);
  SvB_MA_VHH_ps_BDT_kVV  = dir.make<TH1F>("SvB_MA_VHH_ps_BDT_kVV",  (name+"/SvB_MA_VHH_ps_BDT_kVV;  SvB_MA Regressed P(VHH) #kappa_{#lambda} BDT<0; Entries").c_str(), 100, 0, 1);
  SvB_MA_VHH_ps_BDT_kl = dir.make<TH1F>("SvB_MA_VHH_ps_BDT_kl",  (name+"/SvB_MA_VHH_ps_BDT_kl;  SvB_MA Regressed P(VHH) #kappa_{#lambda} BDT#geq 0; Entries").c_str(), 100, 0, 1);

  sSvB_MA_VHH_ps.reset(SvB_MA_VHH_ps);
  sSvB_MA_VHH_ps_BDT_kVV.reset(SvB_MA_VHH_ps_BDT_kVV);
  sSvB_MA_VHH_ps_BDT_kl.reset(SvB_MA_VHH_ps_BDT_kl);

  SvB_MA_VHH_ps_ONNX  = dir.make<TH1F>("SvB_MA_VHH_ps_ONNX",  (name+"/SvB_MA_VHH_ps_ONNX;  SvB_MA Regressed P(VHH); Entries").c_str(), 100, 0, 1);
  SvB_MA_VHH_ps_BDT_kVV_ONNX  = dir.make<TH1F>("SvB_MA_VHH_ps_BDT_kVV_ONNX",  (name+"/SvB_MA_VHH_ps_BDT_kVV_ONNX;  SvB_MA Regressed P(VHH) #kappa_{#lambda} BDT<0; Entries").c_str(), 100, 0, 1);
  SvB_MA_VHH_ps_BDT_kl_ONNX = dir.make<TH1F>("SvB_MA_VHH_ps_BDT_kl_ONNX",  (name+"/SvB_MA_VHH_ps_BDT_kl_ONNX;  SvB_MA Regressed P(VHH) #kappa_{#lambda} BDT#geq 0; Entries").c_str(), 100, 0, 1);


  if(event){
    SvB_MA_VHH_ps_bTagSysts = new systHists(SvB_MA_VHH_ps, event->treeJets->m_btagVariations);
    SvB_MA_VHH_ps_BDT_kVV_bTagSysts = new systHists(SvB_MA_VHH_ps_BDT_kVV, event->treeJets->m_btagVariations);
    SvB_MA_VHH_ps_BDT_kl_bTagSysts = new systHists(SvB_MA_VHH_ps_BDT_kl, event->treeJets->m_btagVariations);

    if(event->treeJets->m_puIdVariations.size() > 0){
      SvB_MA_VHH_ps_puIdSysts = new systHists(SvB_MA_VHH_ps, event->treeJets->m_puIdVariations, "puId");
      SvB_MA_VHH_ps_BDT_kVV_puIdSysts = new systHists(SvB_MA_VHH_ps_BDT_kVV, event->treeJets->m_puIdVariations, "puId");
      SvB_MA_VHH_ps_BDT_kl_puIdSysts = new systHists(SvB_MA_VHH_ps_BDT_kl, event->treeJets->m_puIdVariations, "puId");
    }

    SvB_MA_VHH_ps_zhhNNLOSysts = new systHists(SvB_MA_VHH_ps, event->zhhNNLOVariations, "NNLO");
    SvB_MA_VHH_ps_BDT_kVV_zhhNNLOSysts = new systHists(SvB_MA_VHH_ps_BDT_kVV, event->zhhNNLOVariations, "NNLO");
    SvB_MA_VHH_ps_BDT_kl_zhhNNLOSysts = new systHists(SvB_MA_VHH_ps_BDT_kl, event->zhhNNLOVariations, "NNLO");

    SvB_MA_VHH_ps_ONNX_bTagSysts = new systHists(SvB_MA_VHH_ps_ONNX, event->treeJets->m_btagVariations);
    SvB_MA_VHH_ps_BDT_kVV_ONNX_bTagSysts = new systHists(SvB_MA_VHH_ps_BDT_kVV_ONNX, event->treeJets->m_btagVariations);
    SvB_MA_VHH_ps_BDT_kl_ONNX_bTagSysts = new systHists(SvB_MA_VHH_ps_BDT_kl_ONNX, event->treeJets->m_btagVariations);

    // trigger turn-on systematic

    triggerSyst     = ratioSystHistsProducer::create(sSvB_MA_VHH_ps, "trigger", "sim", "mc_emu");
    triggerSyst_kVV = ratioSystHistsProducer::create(sSvB_MA_VHH_ps_BDT_kVV, "trigger", "sim", "mc_emu");
    triggerSyst_kl  = ratioSystHistsProducer::create(sSvB_MA_VHH_ps_BDT_kl, "trigger", "sim", "mc_emu");
  }
  
  FvT_q_score = dir.make<TH1F>("FvT_q_score", (name+"/FvT_q_score; FvT q_score (main pairing); Entries").c_str(), 100, 0, 1);
  FvT_q_score_dR_min = dir.make<TH1F>("FvT_q_score_dR_min", (name+"/FvT_q_score; FvT q_score (min #DeltaR(j,j) pairing); Entries").c_str(), 100, 0, 1);
  // FvT_q_score_SvB_q_score_max = dir.make<TH1F>("FvT_q_score_SvB_q_score_max", (name+"/FvT_q_score; FvT q_score (max SvB q_score pairing); Entries").c_str(), 100, 0, 1);
  // SvB_q_score = dir.make<TH1F>("SvB_q_score", (name+"/SvB_q_score; SvB q_score; Entries").c_str(), 100, 0, 1);
  // SvB_q_score_FvT_q_score_max = dir.make<TH1F>("SvB_q_score_FvT_q_score_max", (name+"/SvB_q_score; SvB q_score (max FvT q_score pairing); Entries").c_str(), 100, 0, 1);
  // SvB_MA_q_score = dir.make<TH1F>("SvB_MA_q_score", (name+"/SvB_MA_q_score; SvB_MA q_score; Entries").c_str(), 100, 0, 1);

  xHH = dir.make<TH1F>("xHH", (name+"/xHH; X_{HH}; Entries").c_str(), 100, 0, 10);  
  Double_t bins_mHH[] = {100, 216, 237, 260, 286, 314, 345, 379, 416, 457, 502, 552, 607, 667, 733, 806, 886, 974, 1071, 1178, 1295, 1500};
  //mHH = dir.make<TH1F>("mHH", (name+"/mHH; m_{HH} [GeV]; Entries").c_str(), 100, 150,1500);
  mHH = dir.make<TH1F>("mHH", (name+"/mHH; m_{HH} [GeV]; Entries").c_str(), 21, bins_mHH);

  hT   = dir.make<TH1F>("hT", (name+"/hT; hT [GeV]; Entries").c_str(),  100,0,1000);
  hT30 = dir.make<TH1F>("hT30", (name+"/hT30; hT [GeV] (jet Pt > 30 GeV); Entries").c_str(),  100,0,1000);
  L1hT   = dir.make<TH1F>("L1hT", (name+"/L1hT; hT [GeV]; Entries").c_str(),  100,0,1000);
  L1hT30 = dir.make<TH1F>("L1hT30", (name+"/L1hT30; hT [GeV] (L1 jet Pt > 30 GeV); Entries").c_str(),  100,0,1000);
  HLThT   = dir.make<TH1F>("HLThT", (name+"/HLThT; hT [GeV]; Entries").c_str(),  100,0,1000);
  HLThT30 = dir.make<TH1F>("HLThT30", (name+"/HLThT30; hT [GeV] (HLT jet Pt > 30 GeV); Entries").c_str(),  100,0,1000);
  m4j_vs_nViews_eq = dir.make<TH2F>("m4j_vs_nViews_eq", (name+"/m4j_vs_nViews_eq; m_{4j} [GeV]; Number of Event Views; Entries").c_str(), 40,100,1100, 4,-0.5,3.5);
  m4j_vs_nViews_00 = dir.make<TH2F>("m4j_vs_nViews_00", (name+"/m4j_vs_nViews_00; m_{4j} [GeV]; Number of Event Views; Entries").c_str(), 40,100,1100, 4,-0.5,3.5);
  m4j_vs_nViews_01 = dir.make<TH2F>("m4j_vs_nViews_01", (name+"/m4j_vs_nViews_01; m_{4j} [GeV]; Number of Event Views; Entries").c_str(), 40,100,1100, 4,-0.5,3.5);
  m4j_vs_nViews_02 = dir.make<TH2F>("m4j_vs_nViews_02", (name+"/m4j_vs_nViews_02; m_{4j} [GeV]; Number of Event Views; Entries").c_str(), 40,100,1100, 4,-0.5,3.5);
  m4j_vs_nViews_10 = dir.make<TH2F>("m4j_vs_nViews_10", (name+"/m4j_vs_nViews_10; m_{4j} [GeV]; Number of Event Views; Entries").c_str(), 40,100,1100, 4,-0.5,3.5);
  m4j_vs_nViews_11 = dir.make<TH2F>("m4j_vs_nViews_11", (name+"/m4j_vs_nViews_11; m_{4j} [GeV]; Number of Event Views; Entries").c_str(), 40,100,1100, 4,-0.5,3.5);
  m4j_vs_nViews_12 = dir.make<TH2F>("m4j_vs_nViews_12", (name+"/m4j_vs_nViews_12; m_{4j} [GeV]; Number of Event Views; Entries").c_str(), 40,100,1100, 4,-0.5,3.5);

  if(isMC){
    Double_t bins_m4b[] = {100, 112, 126, 142, 160, 181, 205, 232, 263, 299, 340, 388, 443, 507, 582, 669, 770, 888, 1027, 1190, 1381, 1607, 2000};
    truthM4b = dir.make<TH1F>("truthM4b", (name+"/truthM4b; True m_{4b} [GeV]; Entries").c_str(), 21, bins_mZH);
    truthM4b_vs_mZH = dir.make<TH2F>("truthM4b_vs_mZH", (name+"/truthM4b_vs_mZH; True m_{4b} [GeV]; Reconstructed m_{ZH} [GeV];Entries").c_str(), 22, bins_m4b, 22, bins_m4b);
    nTrueBJets = dir.make<TH1F>("nTrueBJets", (name+"/nTrueBJets; Number of true b-jets; Entries").c_str(),  16,-0.5,15.5);
  }

  if(nTupleAnalysis::findSubStr(histDetailLevel,"weightStudy")){
    weightStudy_v0v1  = new weightStudyHists(name+"/FvTStudy_v0v1",  fs, "weight_FvT_3bMix4b_rWbW2_v0_e25_os012", "weight_FvT_3bMix4b_rWbW2_v1_e25_os012", debug);
    weightStudy_v0v9  = new weightStudyHists(name+"/FvTStudy_v0v9",  fs, "weight_FvT_3bMix4b_rWbW2_v0_e25_os012", "weight_FvT_3bMix4b_rWbW2_v9_e25_os012", debug);
    weightStudy_os012 = new weightStudyHists(name+"/FvTStudy_os012", fs, "weight_FvT_3bMix4b_rWbW2_v0_e25",       "weight_FvT_3bMix4b_rWbW2_v0_e25_os012", debug);
    weightStudy_e20   = new weightStudyHists(name+"/FvTStudy_e20",   fs, "weight_FvT_3bMix4b_rWbW2_v0_os012",     "weight_FvT_3bMix4b_rWbW2_v0_e25_os012",       debug);
    //weightStudy_v0v1 = new weightStudyHists(name+"/FvTStudy_v0v1", fs, debug);
  }

  if(nTupleAnalysis::findSubStr(histDetailLevel,"bdtStudy")){
    kl_BDT = dir.make<TH1F>("kl_BDT", (name+"/kl_BDT; #kappa_{#lambda} BDT Output; Entries").c_str(), 32, -1 , 1); 
  }
  
} 

void viewHists::Fill(eventData* event, std::shared_ptr<eventView> &view){//, int nViews, int nViews_10, int nViews_11, int nViews_12){
  //
  // Object Level
  //
  nAllJets->Fill(event->allJets.size(), event->weight);
  nAllNotCanJets->Fill(event->nAllNotCanJets, event->weight);
  st->Fill(event->st, event->weight);
  stNotCan->Fill(event->stNotCan, event->weight);
  nSelJets->Fill(event->nSelJets, event->weight);
  nSelJets_noBTagSF->Fill(event->nSelJets, event->weight/event->bTagSF);
  if     (event->s4j < 320) nSelJets_lowSt ->Fill(event->nSelJets, event->weight);
  else if(event->s4j < 450) nSelJets_midSt ->Fill(event->nSelJets, event->weight);
  else                      nSelJets_highSt->Fill(event->nSelJets, event->weight);
  if(event->pseudoTagWeight < 1e-6) std::cout << "viewHists::Fill WARNING event->pseudoTagWeight " << event->pseudoTagWeight << std::endl;
  float weightDividedByPseudoTagWeight = (event->pseudoTagWeight > 0) ? event->weight/event->pseudoTagWeight : 0;
  if(debug) std::cout << "viewHists::Fill event->weight " << event->weight << " event->pseudoTagWeight " << event->pseudoTagWeight << " weightDividedByPseudoTagWeight " << weightDividedByPseudoTagWeight << std::endl;
  nSelJetsUnweighted->Fill(event->nSelJets, weightDividedByPseudoTagWeight);
  if     (event->s4j < 320) nSelJetsUnweighted_lowSt ->Fill(event->nSelJets, weightDividedByPseudoTagWeight);//these depend only on FvT classifier ratio spline
  else if(event->s4j < 450) nSelJetsUnweighted_midSt ->Fill(event->nSelJets, weightDividedByPseudoTagWeight);
  else                      nSelJetsUnweighted_highSt->Fill(event->nSelJets, weightDividedByPseudoTagWeight);
  nTagJets->Fill(event->nTagJets, event->weight); 
  nTagJetsUnweighted->Fill(event->nTagJets, weightDividedByPseudoTagWeight);
  nPSTJets->Fill(event->nPSTJets, event->weight);
  if     (event->s4j < 320) nPSTJets_lowSt ->Fill(event->nPSTJets, event->weight);
  else if(event->s4j < 450) nPSTJets_midSt ->Fill(event->nPSTJets, event->weight);
  else                      nPSTJets_highSt->Fill(event->nPSTJets, event->weight);
  nPSTJetsUnweighted->Fill(event->nPSTJets, weightDividedByPseudoTagWeight);
  nCanJets->Fill(event->canJets.size(), event->weight);

  hT  ->Fill(event->ht,   event->weight);
  hT30->Fill(event->ht30, event->weight);

  if(debug) std::cout << "viewHists::Fill seljets " << std::endl;
  for(auto &jet: event->selJets) selJets->Fill(jet, event->weight);
  if(debug) std::cout << "viewHists::Fill tagjets " << std::endl;
  for(auto &jet: event->tagJets) tagJets->Fill(jet, event->weight);
  for(auto &jet: event->canJets) canJets->Fill(jet, event->weight);
  for(auto &jet: event->allNotCanJets) allNotCanJets->Fill(jet, event->weight);
  canJet0->Fill(event->canJets[0], event->weight);
  canJet1->Fill(event->canJets[1], event->weight);
  canJet2->Fill(event->canJets[2], event->weight);
  canJet3->Fill(event->canJets[3], event->weight);
  for(auto &jet: event->othJets) othJets->Fill(jet, event->weight);
  for(auto &jet: event->canVJets) canVJets->Fill(jet, event->weight);
  if(event->canVJets.size() == 2){
    canVJet0->Fill(event->canVJets[0], event->weight);
    canVJet1->Fill(event->canVJets[1], event->weight);
  }

  nTruVJets->Fill(event->truVJets.size(), event->weight);
  for(auto &jet: event->truVJets) truVJets->Fill(jet, event->weight);
  nCanHTruVJets->Fill(event->canHTruVJets.size(), event->weight);
  for(auto &dijet: event->canVDijets) canVDijets->Fill(dijet, event->weight);
  nCanVDijets->Fill(event->canVDijets.size(), event->weight);

  aveAbsEta->Fill(event->aveAbsEta, event->weight);
  aveAbsEtaOth->Fill(event->aveAbsEtaOth, event->weight);

  if(allTrigJets){
    for(auto &trigjet: event->allTrigJets) allTrigJets->Fill(trigjet, event->weight);
    L1hT  ->Fill(event->L1ht,   event->weight);
    L1hT30->Fill(event->L1ht30, event->weight);

    HLThT  ->Fill(event->HLTht,   event->weight);
    HLThT30->Fill(event->HLTht30, event->weight);
  }

  if(debug) std::cout << "viewHists::Fill muons " << std::endl;

  nAllMuons->Fill(event->allMuons.size(), event->weight);
  nIsoMed25Muons->Fill(event->muons_isoMed25.size(), event->weight);
  nIsoMed40Muons->Fill(event->muons_isoMed40.size(), event->weight);
  for(auto &muon: event->allMuons) allMuons->Fill(muon, event->weight);
  for(auto &muon: event->muons_isoMed25) muons_isoMed25->Fill(muon, event->weight);
  for(auto &muon: event->muons_isoMed40) muons_isoMed40->Fill(muon, event->weight);

  nAllElecs->Fill(event->allElecs.size(), event->weight);
  nIsoMed25Elecs->Fill(event->elecs_isoMed25.size(), event->weight);
  nIsoMed40Elecs->Fill(event->elecs_isoMed40.size(), event->weight);
  for(auto &elec: event->allElecs)             allElecs->Fill(elec, event->weight);
  for(auto &elec: event->elecs_isoMed25) elecs_isoMed25->Fill(elec, event->weight);
  for(auto &elec: event->elecs_isoMed40) elecs_isoMed40->Fill(elec, event->weight);



  lead  ->Fill(view->lead,   event->weight);
  subl  ->Fill(view->subl,   event->weight);
  lead_m_vs_subl_m->Fill(view->lead->m, view->subl->m, event->weight);

  leadSt->Fill(view->leadSt, event->weight);
  sublSt->Fill(view->sublSt, event->weight);
  leadSt_m_vs_sublSt_m->Fill(view->leadSt->m, view->sublSt->m, event->weight);
  m4j_vs_leadSt_dR->Fill(view->m4j, view->leadSt->dR, event->weight);
  m4j_vs_sublSt_dR->Fill(view->m4j, view->sublSt->dR, event->weight);

  leadM ->Fill(view->leadM,  event->weight);
  sublM ->Fill(view->sublM,  event->weight);
  leadM_m_vs_sublM_m->Fill(view->leadM->m, view->sublM->m, event->weight);

  close ->Fill(event->close,  event->weight);
  other ->Fill(event->other,  event->weight);
  close_m_vs_other_m->Fill(event->close->m, event->other->m, event->weight);

  if(allBJets){
    for(auto& jet:event->allBJets) allBJets->Fill(jet->pt, jet->eta, 1);
    for(auto& jet:event->allNotBJets) allNotBJets->Fill(jet->pt, jet->eta, 1);
    for(auto& jet:event->allBJetsPassPuId) allBJetsPassPuId->Fill(jet->pt, jet->eta, 1);
    for(auto& jet:event->allNotBJetsPassPuId) allNotBJetsPassPuId->Fill(jet->pt, jet->eta, 1);

    for(auto& jet:event->allPUBJets) allPUBJets->Fill(jet->pt, jet->eta, 1);
    for(auto& jet:event->allPUBJetsPassPuId) allPUBJetsPassPuId->Fill(jet->pt, jet->eta, 1);
    for(auto& jet:event->allPUNotBJets) allPUNotBJets->Fill(jet->pt, jet->eta, 1);
    for(auto& jet:event->allPUNotBJetsPassPuId) allPUNotBJetsPassPuId->Fill(jet->pt, jet->eta, 1);
  }

  //
  // Event Level
  //
  nPVs->Fill(event->nPVs, event->weight);
  nPVsGood->Fill(event->nPVsGood, event->weight);
  v4j->Fill(view->p, event->weight);
  s4j->Fill(event->s4j, event->weight);
  r4j->Fill(view->pt/event->s4j, event->weight);
  // m123->Fill(event->m123, event->weight);
  // m023->Fill(event->m023, event->weight);
  // m013->Fill(event->m013, event->weight);
  // m012->Fill(event->m012, event->weight);
  dBB->Fill(view->dBB, event->weight);
  dEtaBB->Fill(view->dEtaBB, event->weight);
  dRBB->Fill(view->dRBB, event->weight);
  xZZ->Fill(view->xZZ, event->weight);
  mZZ->Fill(view->mZZ, event->weight);
  xZH->Fill(view->xZH, event->weight);
  mZH->Fill(view->mZH, event->weight);
  xHH->Fill(view->xHH, event->weight);
  mHH->Fill(view->mHH, event->weight);

  xWt0->Fill(event->xWt0, event->weight);
  xWt1->Fill(event->xWt1, event->weight);
  //xWt2->Fill(event->xWt2, event->weight);
  xWt ->Fill(event->xWt,  event->weight);
  t0->Fill(event->t0, event->weight);
  t1->Fill(event->t1, event->weight);
  //t2->Fill(event->t2, event->weight);
  t ->Fill(event->t,  event->weight);

  FvT->Fill(event->FvT, event->weight);
  FvTUnweighted->Fill(event->FvT, event->weight/event->reweight); // depends only on jet combinatoric model
  // FvT_pd4->Fill(event->FvT_pd4, event->weight);
  // FvT_pd3->Fill(event->FvT_pd3, event->weight);
  // FvT_pt4->Fill(event->FvT_pt4, event->weight);
  // FvT_pt3->Fill(event->FvT_pt3, event->weight);
  // FvT_pm4->Fill(event->FvT_pm4, event->weight);
  // FvT_pm3->Fill(event->FvT_pm3, event->weight);
  // FvT_pt ->Fill(event->FvT_pt,  event->weight);
  // FvT_std->Fill(event->FvT_std, event->weight);
  // if(event->FvT) FvT_ferr->Fill(event->FvT_std/event->FvT, event->weight);
  // SvB_ps ->Fill(event->SvB_ps , event->weight);
  // if(SvB_ps_bTagSysts){
  //   SvB_ps_bTagSysts->Fill(event->SvB_ps, event->weight/event->bTagSF, event->treeJets->m_btagSFs);
  // }
  // SvB_pwhh->Fill(event->SvB_pwhh, event->weight);
  // SvB_pzhh->Fill(event->SvB_pzhh, event->weight);
  // SvB_ptt->Fill(event->SvB_ptt, event->weight);


  // SvB_MA_ps ->Fill(event->SvB_MA_ps , event->weight);
  // if(SvB_MA_ps_bTagSysts){
  //   SvB_MA_ps_bTagSysts->Fill(event->SvB_MA_ps, event->weight/event->bTagSF, event->treeJets->m_btagSFs);
  // }
  // SvB_MA_pwhh->Fill(event->SvB_MA_pwhh, event->weight);
  // SvB_MA_pzhh->Fill(event->SvB_MA_pzhh, event->weight);
  // SvB_MA_ptt->Fill(event->SvB_MA_ptt, event->weight);

  // if(event->SvB_MA_pwhh<event->SvB_MA_pzhh){
  //   SvB_MA_ps_zhh->Fill(event->SvB_MA_ps, event->weight);
  // }else{
  //   SvB_MA_ps_whh->Fill(event->SvB_MA_ps, event->weight);
  // }


  FvT_q_score->Fill(view->FvT_q_score, event->weight);
  FvT_q_score_dR_min->Fill(event->view_dR_min->FvT_q_score, event->weight);
  // FvT_q_score_SvB_q_score_max->Fill(event->view_max_SvB_q_score->FvT_q_score, event->weight);
  // SvB_q_score->Fill(view->SvB_q_score, event->weight);
  // SvB_q_score_FvT_q_score_max->Fill(event->view_max_FvT_q_score->SvB_q_score, event->weight);
  // SvB_MA_q_score->Fill(view->SvB_MA_q_score, event->weight);

  // FvT_SvB_q_score_max_same->Fill((float)(event->view_max_FvT_q_score==event->view_max_SvB_q_score), event->weight);

  puIdSF->Fill(event->puIdSF, event->weight);
  SvB_MA_VHH_ps->Fill(event->SvB_MA_VHH_ps, event->weight);
  SvB_MA_VHH_ps_ONNX->Fill(event->SvB_MA_ps_ONNX, event->weight);
  if(triggerSyst){
    triggerSyst->fill(event->SvB_MA_VHH_ps, event->weightNoTrigger * event->trigWeight_Flag, event->weightNoTrigger * event->trigWeight_MC);
  }
  if(SvB_MA_VHH_ps_bTagSysts){
    SvB_MA_VHH_ps_bTagSysts->Fill(event->SvB_MA_VHH_ps, event->weight, event->treeJets->m_btagSFs, event->bTagSF);
  }
  if(SvB_MA_VHH_ps_puIdSysts){
    SvB_MA_VHH_ps_puIdSysts->Fill(event->SvB_MA_VHH_ps, event->weight, event->treeJets->m_puIdSFs, event->puIdSF);
  }
  if(SvB_MA_VHH_ps_zhhNNLOSysts){
    SvB_MA_VHH_ps_zhhNNLOSysts->Fill(event->SvB_MA_VHH_ps, event->weight, event->zhhNNLOSFs, event->zhhNNLOSFs["central"]);
  }
  if(SvB_MA_VHH_ps_ONNX_bTagSysts){
    SvB_MA_VHH_ps_ONNX_bTagSysts->Fill(event->SvB_MA_ps_ONNX, event->weight, event->treeJets->m_btagSFs, event->bTagSF);
  }
  if(event->BDT_kl<0 && event->BDT_kl>=-1){
    SvB_MA_VHH_ps_BDT_kVV->Fill(event->SvB_MA_VHH_ps, event->weight);
    SvB_MA_VHH_ps_BDT_kVV_ONNX->Fill(event->SvB_MA_ps_ONNX, event->weight);
    if(triggerSyst_kVV){
      triggerSyst_kVV->fill(event->SvB_MA_VHH_ps, event->weightNoTrigger * event->trigWeight_Flag, event->weightNoTrigger * event->trigWeight_MC);
    }
    if(SvB_MA_VHH_ps_BDT_kVV_bTagSysts){
      SvB_MA_VHH_ps_BDT_kVV_bTagSysts->Fill(event->SvB_MA_VHH_ps, event->weight, event->treeJets->m_btagSFs, event->bTagSF);
    }
    if(SvB_MA_VHH_ps_BDT_kVV_puIdSysts){
      SvB_MA_VHH_ps_BDT_kVV_puIdSysts->Fill(event->SvB_MA_VHH_ps, event->weight, event->treeJets->m_puIdSFs, event->puIdSF);
    }
    if(SvB_MA_VHH_ps_BDT_kVV_zhhNNLOSysts){
      SvB_MA_VHH_ps_BDT_kVV_zhhNNLOSysts->Fill(event->SvB_MA_VHH_ps, event->weight, event->zhhNNLOSFs, event->zhhNNLOSFs["central"]);
    }
    if(SvB_MA_VHH_ps_BDT_kVV_ONNX_bTagSysts){
      SvB_MA_VHH_ps_BDT_kVV_ONNX_bTagSysts->Fill(event->SvB_MA_ps_ONNX, event->weight, event->treeJets->m_btagSFs, event->bTagSF);
    }
  }
  if(event->BDT_kl>=0){
    SvB_MA_VHH_ps_BDT_kl->Fill(event->SvB_MA_VHH_ps, event->weight);
    SvB_MA_VHH_ps_BDT_kl_ONNX->Fill(event->SvB_MA_ps_ONNX, event->weight);
    if(triggerSyst_kl){
      triggerSyst_kl->fill(event->SvB_MA_VHH_ps, event->weightNoTrigger * event->trigWeight_Flag, event->weightNoTrigger * event->trigWeight_MC);
    }
    if(SvB_MA_VHH_ps_BDT_kl_bTagSysts){
      SvB_MA_VHH_ps_BDT_kl_bTagSysts->Fill(event->SvB_MA_VHH_ps, event->weight, event->treeJets->m_btagSFs, event->bTagSF);
    }
    if(SvB_MA_VHH_ps_BDT_kl_puIdSysts){
      SvB_MA_VHH_ps_BDT_kl_puIdSysts->Fill(event->SvB_MA_VHH_ps, event->weight, event->treeJets->m_puIdSFs, event->puIdSF);
    }
    if(SvB_MA_VHH_ps_BDT_kl_zhhNNLOSysts){
      SvB_MA_VHH_ps_BDT_kl_zhhNNLOSysts->Fill(event->SvB_MA_VHH_ps, event->weight, event->zhhNNLOSFs, event->zhhNNLOSFs["central"]);
    }
    if(SvB_MA_VHH_ps_BDT_kl_ONNX_bTagSysts){
      SvB_MA_VHH_ps_BDT_kl_ONNX_bTagSysts->Fill(event->SvB_MA_ps_ONNX, event->weight, event->treeJets->m_btagSFs, event->bTagSF);
    }
  }

  if(kl_BDT && event->canVDijets.size() > 0){
    kl_BDT->Fill(event->BDT_kl, event->weight);
  }


  m4j_vs_nViews_eq->Fill(view->m4j, event->nViews_eq, event->weight);
  if(view->passDijetMass){
    if      (view->passLeadStMDR && view->passSublStMDR){ m4j_vs_nViews_12->Fill(view->m4j, event->nViews_12, event->weight); 
    }else if(view->passLeadStMDR || view->passSublStMDR){ m4j_vs_nViews_11->Fill(view->m4j, event->nViews_11, event->weight); 
    }else                                               { m4j_vs_nViews_10->Fill(view->m4j, event->nViews_10, event->weight); }
  }else{
    if      (view->passLeadStMDR && view->passSublStMDR){ m4j_vs_nViews_02->Fill(view->m4j, event->nViews_02, event->weight); 
    }else if(view->passLeadStMDR || view->passSublStMDR){ m4j_vs_nViews_01->Fill(view->m4j, event->nViews_01, event->weight); 
    }else                                               { m4j_vs_nViews_00->Fill(view->m4j, event->nViews_00, event->weight); }
  }

  if(event->truth != NULL){
    truthM4b       ->Fill(event->truth->m4b,            event->weight);
    truthM4b_vs_mZH->Fill(event->truth->m4b, view->mZH, event->weight);
    nTrueBJets->Fill(event->nTrueBJets, event->weight);
  }

  if(weightStudy_v0v1)  weightStudy_v0v1 ->Fill(event, view);
  if(weightStudy_v0v9)  weightStudy_v0v9 ->Fill(event, view);
  if(weightStudy_os012) weightStudy_os012->Fill(event, view);
  if(weightStudy_e20)   weightStudy_e20  ->Fill(event, view);

  if(debug) std::cout << "viewHists::Fill done " << std::endl;
  return;
}

viewHists::~viewHists(){} 

