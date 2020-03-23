//#include "TChain.h"
#include "ZZ4b/nTupleAnalysis/interface/cutflowHists.h"
#include <string>

using namespace nTupleAnalysis;

cutflowHists::cutflowHists(std::string name, fwlite::TFileService& fs, bool isMC) {

  dir = fs.mkdir(name);
  unitWeight = dir.make<TH1F>("unitWeight", (name+"/unitWeight; ;Entries").c_str(),  1,1,2);
  unitWeight->SetCanExtend(1);

  Mu1_NoPt = dir.make<TH1F>("Mu1_NoPt", (name+"At Least One Muon, no Pt Cut; At least one muon?; Entries").c_str()     , 2,0,2);
  Mu2_NoPt = dir.make<TH1F>("Mu2_NoPt", (name+"At Least Two Muons, no Pt Cut; At least two muons?; Entries").c_str()   , 2,0,2);
  Mu1_5GeV = dir.make<TH1F>("Mu1_5GeV", (name+"At Least One Muon, Pt >= 5 GeV; At least one muon?; Entries").c_str()   , 2,0,2);
  Mu2_5GeV = dir.make<TH1F>("Mu2_5GeV", (name+"At Least Two Muons, Pt >= 5 GeV; At least two muons?; Entries").c_str() , 2,0,2);

  int massCut = 300 ; //Trying 300 now

  MC = dir.make<TH1F>("MC","MC Efficiencies;;Entries",1,1,2);
  MC->SetCanExtend(1);

  muTrigs_noMC = dir.make<TH1F>("muTrigs_noMC", (name+"/#mu Trigs, SR, |#eta| < 1.5, Didn't pass MC; ; Entries").c_str(),1,1,2);
  muTrigs_noMC -> SetCanExtend(1);
  muTrigs_HiMass_noMC = dir.make<TH1F>("muTrigs_HiMass_noMC", (name+"/#mu Trigs, SR, |#eta| < 1.5, m4b > " + std::__cxx11::to_string(massCut) + " GeV, Didn't pass MC; ; Entries").c_str(),1,1,2);
  muTrigs_HiMass_noMC -> SetCanExtend(1);
  muTrigs_LoMass_noMC = dir.make<TH1F>("muTrigs_LoMass_noMC", (name+"/#mu Trigs, SR, |#eta| < 1.5, m4b < " + std::__cxx11::to_string(massCut) + " GeV,\
 Didn't pass MC; ; Entries").c_str(),1,1,2);
  muTrigs_LoMass_noMC -> SetCanExtend(1);

  muTrigs_noMC_sip = dir.make<TH1F>("muTrigs_noMC_sip", (name+"/#mu Trigs, SR, |#eta| < 1.5, No MC, sip3d cut; ; Entries").c_str(),1,1,2);
  muTrigs_noMC_sip -> SetCanExtend(1);
  muTrigs_HiMass_noMC_sip = dir.make<TH1F>("muTrigs_HiMass_noMC_sip", (name+"/#mu Trigs, SR, |#eta| < 1.5, m4b > " + std::__cxx11::to_string(massCut) + " GeV, No MC, sip3d cut; ; Entries").c_str(),1,1,2);
  muTrigs_HiMass_noMC_sip -> SetCanExtend(1);
  muTrigs_LoMass_noMC_sip = dir.make<TH1F>("muTrigs_LoMass_noMC_sip", (name+"/#mu Trigs, SR, |#eta| < 1.5, m4b < " + std::__cxx11::to_string(massCut) + " GeV, No MC, sip3d cut; ; Entries").c_str(),1,1,2);
  muTrigs_LoMass_noMC_sip -> SetCanExtend(1);

  muonTrigs = dir.make<TH1F>("muonTrigs",(name+"/Muon Triggers (SR only), |#eta| < 1.5; ; Entries").c_str(), 1,1,2);
  muonTrigs->SetCanExtend(1);
  muonTrigsHiMass = dir.make<TH1F>("muonTrigsHiMass",(name+"/Muon Triggers (SR, |#eta| < 1.5, m4b > " + std::__cxx11::to_string(massCut) + " GeV,\
 Didn't pass MC; ; Entries").c_str(),1,1,2);
  muonTrigsHiMass->SetCanExtend(1);
  muonTrigsLoMass = dir.make<TH1F>("muonTrigsLoMass",(name+"/Muon Triggers (SR, |#eta| < 1.5, m4b < " + std::__cxx11::to_string(massCut) + " GeV,\
 Didn't pass MC; ; Entries").c_str(),1,1,2);
  muonTrigsLoMass->SetCanExtend(1);

  muonPt      = dir.make<TH1F>("muonPt",       "Muon Pt (SR, |#eta| < 1.5); pt [GeV];Entries"                         ,100,0,150);
  Muon_ip3d   = dir.make<TH1F>("Muon ip3d",    "Muon ip3d (SR, |#eta| < 1.5);ip3d [cm];Entries"                       ,100,0,0.6);
  Muon_dxy    = dir.make<TH1F>("Muon dxy",     "Muon dxy (SR, |#eta| < 1.5);dxy [cm];Entries"                         ,100,-0.5,0.5);
  Muon_sip3d  = dir.make<TH1F>("Muon sip3d",   "Muon sip3d (SR, |#eta| < 1.5);sip3d [cm];Entries"                     ,100,0,150);
  Muon_dxyErr = dir.make<TH1F>("Muon dxyErr",  "Muon dxy/dxyErr (SR, |#eta| < 1.5);Significance;Entries"              ,100,-100,100);
  Mu_pt_7     = dir.make<TH1F>("Muon pt7",     "Muon Pt (SR, |#eta| < 1.5), pt > 7 GeV);pt [GeV];Entries"             ,100,0,150);
  Mu_ip3d_7   = dir.make<TH1F>("Muon ip3d7",   "Muon ip3d (SR, |#eta| < 1.5, pt > 7 GeV);ip3d [cm];Entries"           ,100,0,0.6);
  Mu_dxy_7    = dir.make<TH1F>("Muon dxy7",    "Muon dxy (SR, |#eta| < 1.5, pt > 7 GeV);dxy [cm];Entries"             ,100,-0.5,0.5);
  Mu_sip3d_7  = dir.make<TH1F>("Muon sip3d7",  "Muon sip3d (SR, |#eta| < 1.5, pt > 7 GeV);sip3d [cm];Entries"         ,100,0,150);
  Mu_dxyErr_7 = dir.make<TH1F>("Muon dxyErr7", "Muon dxy/dxyErr (SR, |#eta| < 1.5, pt > 7 GeV);Significance;Entries"  ,100,-100,100);
  Mu_pt_8     = dir.make<TH1F>("Muon pt8",     "Muon Pt (SR, |#eta| < 1.5), pt > 8 GeV);pt [GeV];Entries"             ,100,0,150);
  Mu_ip3d_8   = dir.make<TH1F>("Muon ip3d8",   "Muon ip3d (SR, |#eta| < 1.5, pt > 8 GeV);ip3d [cm];Entries"           ,100,0,0.6);
  Mu_dxy_8    = dir.make<TH1F>("Muon dxy8",    "Muon dxy (SR, |#eta| < 1.5, pt > 8 GeV);dxy [cm];Entries"             ,100,-0.5,0.5);
  Mu_sip3d_8  = dir.make<TH1F>("Muon sip3d8",  "Muon sip3d (SR, |#eta| < 1.5, pt > 8 GeV);sip3d [cm];Entries"         ,100,0,150);
  Mu_dxyErr_8 = dir.make<TH1F>("Muon dxyErr8", "Muon dxy/dxyErr (SR, |#eta| < 1.5, pt > 8 GeV);Significance;Entries"  ,100,-100,100);
  Mu_pt_9     = dir.make<TH1F>("Muon pt9",     "Muon Pt (SR, |#eta| < 1.5), pt > 9 GeV);pt [GeV];Entries"             ,100,0,150);
  Mu_ip3d_9   = dir.make<TH1F>("Muon ip3d9",   "Muon ip3d (SR, |#eta| < 1.5, pt > 9 GeV);ip3d [cm];Entries"           ,100,0,0.6);
  Mu_dxy_9    = dir.make<TH1F>("Muon dxy9",    "Muon dxy (SR, |#eta| < 1.5, pt > 9 GeV);dxy [cm];Entries"             ,100,-0.5,0.5);
  Mu_sip3d_9  = dir.make<TH1F>("Muon sip3d9",  "Muon sip3d (SR, |#eta| < 1.5, pt > 9 GeV);sip3d [cm];Entries"         ,100,0,150);
  Mu_dxyErr_9 = dir.make<TH1F>("Muon dxyErr9", "Muon dxy/dxyErr (SR, |#eta| < 1.5, pt > 9 GeV);Significance;Entries"  ,100,-100,100);
  Mu_pt_12    = dir.make<TH1F>("Muon pt12",    "Muon Pt (SR, |#eta| < 1.5), pt > 12 GeV);pt [GeV];Entries"            ,100,0,150);
  Mu_ip3d_12  = dir.make<TH1F>("Muon ip3d12",  "Muon ip3d (SR, |#eta| < 1.5, pt > 12 GeV);ip3d [cm];Entries"          ,100,0,0.6);
  Mu_dxy_12   = dir.make<TH1F>("Muon dxy12",   "Muon dxy (SR, |#eta| < 1.5, pt > 12 GeV);dxy [cm];Entries"            ,100,-0.5,0.5);
  Mu_sip3d_12 = dir.make<TH1F>("Muon sip3d12", "Muon sip3d (SR, |#eta| < 1.5, pt > 12 GeV);sip3d [cm];Entries"        ,100,0,150);
  Mu_dxyErr_12= dir.make<TH1F>("Muon dxyErr12","Muon dxy/dxyErr (SR, |#eta| < 1.5, pt > 12 GeV);Significance;Entries" ,100,-100,100);

  sip3d_Mu12_IP6 = dir.make<TH1F>("sip_Mu12_IP6","Muon sip3d (SR, |#eta| < 1.5, pass HLT_Mu12_IP6_part0 trigger);sip3d;Entries",100,0,150);
  sip3d_Mu9_IP6 = dir.make<TH1F>("sip_Mu9_IP6","Muon sip3d (SR, |#eta| < 1.5, pass HLT_Mu9_IP6_part0 trigger);sip3d;Entries",100,0,150);
  sip3d_Mu9_IP5 = dir.make<TH1F>("sip_Mu9_IP5","Muon sip3d (SR, |#eta| < 1.5, pass HLT_Mu9_IP5_part0 trigger);sip3d;Entries",100,0,150);
  sip3d_Mu9_IP4 = dir.make<TH1F>("sip_Mu9_IP4","Muon sip3d (SR, |#eta| < 1.5, pass HLT_Mu9_IP4_part0 trigger);sip3d;Entries",100,0,150);
  sip3d_Mu8_IP6 = dir.make<TH1F>("sip_Mu8_IP6","Muon sip3d (SR, |#eta| < 1.5, pass HLT_Mu8_IP6_part0 trigger);sip3d;Entries",100,0,150);
  sip3d_Mu8_IP5 = dir.make<TH1F>("sip_Mu8_IP5","Muon sip3d (SR, |#eta| < 1.5, pass HLT_Mu8_IP5_part0 trigger);sip3d;Entries",100,0,150);
  sip3d_Mu8_IP3 = dir.make<TH1F>("sip_Mu8_IP3","Muon sip3d (SR, |#eta| < 1.5, pass HLT_Mu8_IP3_part0 trigger);sip3d;Entries",100,0,150);
  sip3d_Mu7_IP4 = dir.make<TH1F>("sip_Mu7_IP4","Muon sip3d (SR, |#eta| < 1.5, pass HLT_Mu7_IP4_part0 trigger);sip3d;Entries",100,0,150);

  weighted = dir.make<TH1F>("weighted", (name+"/weighted; ;Entries").c_str(),  1,1,2);
  weighted->SetCanExtend(1);

  AddCut("all");

  if(isMC){
    //Make a weighted cutflow as a function of the true m4b, xaxis is m4b, yaxis is cut name. 
    Double_t bins_m4b[] = {100, 112, 126, 142, 160, 181, 205, 232, 263, 299, 340, 388, 443, 507, 582, 669, 770, 888, 1027, 1190, 1381, 1607, 2000};
    truthM4b = dir.make<TH2F>("truthM4b", (name+"/truthM4b; Truth m_{4b} [GeV]; ;Entries").c_str(), 22, bins_m4b, 1, 1, 2);
    truthM4b->SetCanExtend(TH1::kYaxis);
    truthM4b->GetYaxis()->FindBin("all");
    truthM4b->GetXaxis()->SetAlphanumeric(0);
  }
} 

void cutflowHists::AddCut(std::string cut){
  unitWeight->GetXaxis()->FindBin(cut.c_str());  
  weighted->GetXaxis()->FindBin(cut.c_str());
  unitWeight->GetXaxis()->FindBin((cut+"_HLT").c_str());  
  weighted->GetXaxis()->FindBin((cut+"_HLT").c_str());
}

void cutflowHists::BasicFill(const std::string& cut, eventData* event, float weight){
  unitWeight->Fill(cut.c_str(), 1);
  weighted  ->Fill(cut.c_str(), weight);
  if(truthM4b != NULL) 
    truthM4b->Fill(event->truth->m4b, cut.c_str(), weight);
  return;
}

void cutflowHists::BasicFill(const std::string& cut, eventData* event){
  BasicFill(cut, event, event->weight);
  return;
}

void cutflowHists::Fill(const std::string& cut, eventData* event){

  //Cut+Trigger
  if(event->doTrigEmulation){
    BasicFill(cut, event, event->weightNoTrigger);
    BasicFill(cut+"_HLT_HT330_4j_75_60_45_40_3b", event);
    BasicFill(cut+"_HLT", event);

  }else{
    BasicFill(cut, event);
    if(event->passL1)                      BasicFill(cut+"_L1", event);
    if(event->HLT_HT330_4j_75_60_45_40_3b) BasicFill(cut+"_HLT_HT330_4j_75_60_45_40_3b", event);
    if(event->HLT_4j_103_88_75_15_2b_VBF1) BasicFill(cut+"_HLT_4j_103_88_75_15_2b_VBF1", event);
    if(event->HLT_4j_103_88_75_15_1b_VBF2) BasicFill(cut+"_HLT_4j_103_88_75_15_1b_VBF2", event);
    if(event->HLT_2j116_dEta1p6_2b)        BasicFill(cut+"_HLT_2j116_dEta1p6_2b", event);
    if(event->HLT_J330_m30_2b)             BasicFill(cut+"_HLT_J330_m30_2b", event);
    if(event->HLT_j500)                    BasicFill(cut+"_HLT_j500", event);
    if(event->HLT_2j300ave)                BasicFill(cut+"_HLT_2j300ave", event);
    if(event->passHLT)                     BasicFill(cut+"_HLT", event);
  }

  float massCut = 300.;

  if(event->views.size()>0){
    
    //Cut+SR
    if(event->views[0]->SR){
      for (auto &muon: event -> allMuons){
	if(fabs(muon -> eta) < 1.5){
	  float Pt     = muon -> pt;
	  float Ip3d   = muon -> ip3d;
	  float Sip3d  = muon -> sip3d;
	  //std::cout<<Ip3d<<std::endl;
	  float Dxy    = muon -> dxy;
	  //	  std::cout<<"dxy = "<<std::endl;
	  //std::cout<<Dxy<<std::endl;

	  if(event -> HLT_Mu12_IP6_part0) sip3d_Mu12_IP6 -> Fill(Sip3d);
	  if(event -> HLT_Mu9_IP6_part0)  sip3d_Mu9_IP6  -> Fill(Sip3d);
	  if(event -> HLT_Mu9_IP5_part0)  sip3d_Mu9_IP5  -> Fill(Sip3d);
	  if(event -> HLT_Mu9_IP4_part0)  sip3d_Mu9_IP4  -> Fill(Sip3d);
	  if(event -> HLT_Mu8_IP6_part0)  sip3d_Mu8_IP6  -> Fill(Sip3d);
	  if(event -> HLT_Mu8_IP5_part0)  sip3d_Mu8_IP5  -> Fill(Sip3d);
	  if(event -> HLT_Mu8_IP3_part0)  sip3d_Mu8_IP3  -> Fill(Sip3d);
	  if(event -> HLT_Mu7_IP4_part0)  sip3d_Mu7_IP4  -> Fill(Sip3d);

	  float DxyErr = (Dxy/(muon -> dxyErr));
	  muonPt      -> Fill(Pt);
	  Muon_ip3d   -> Fill(Ip3d);
	  Muon_sip3d  -> Fill(Sip3d);
	  Muon_dxy    -> Fill(Dxy);
	  Muon_dxyErr -> Fill(DxyErr);
	  if (Pt > 7){
	    Mu_pt_7     -> Fill(Pt);
	    Mu_ip3d_7   -> Fill(Ip3d);
	    Mu_sip3d_7  -> Fill(Sip3d);
	    Mu_dxy_7    -> Fill(Dxy);
	    Mu_dxyErr_7 -> Fill(DxyErr);
	  }
	  if (Pt > 8){
	    Mu_pt_8     -> Fill(Pt);
	    Mu_ip3d_8   -> Fill(Ip3d);
	    Mu_sip3d_8  -> Fill(Sip3d);
	    Mu_dxy_8    -> Fill(Dxy);
	    Mu_dxyErr_8 -> Fill(DxyErr);	  
	  }
	  if (Pt > 9){
	    Mu_pt_9     -> Fill(Pt);
	    Mu_ip3d_9   -> Fill(Ip3d);
	    Mu_sip3d_9  -> Fill(Sip3d);
	    Mu_dxy_9    -> Fill(Dxy);
	    Mu_dxyErr_9 -> Fill(DxyErr);
	  }
	  if (Pt > 12){
	    Mu_pt_12     -> Fill(Pt);
	    Mu_ip3d_12   -> Fill(Ip3d);
	    Mu_sip3d_12  -> Fill(Sip3d);
	    Mu_dxy_12    -> Fill(Dxy);
	    Mu_dxyErr_12 -> Fill(DxyErr);
	  }

	}
      }
      //Fill Muon Trigger Hists, only if doTrigEmulation
      if(event -> doTrigEmulation){
	muonTrigs -> Fill("Total",event -> weight);
	double mass = event -> truth -> m4b;
	if(mass < massCut){ muonTrigsLoMass -> Fill("Total",event -> weight); }
	else{muonTrigsHiMass -> Fill("Total",event -> weight); }
	if(event -> allMuons.size() > 0){
	  double pt = event -> allMuons.at(0) -> pt;
	  if (fabs(event -> allMuons.at(0) -> eta) < 1.5){
	      if (pt > 7) muonTrigs -> Fill("7",event -> weight);
	    if (pt > 8) muonTrigs -> Fill("8",event -> weight);
	    if (pt > 9) muonTrigs -> Fill("9",event -> weight);
	    if (pt > 12) muonTrigs -> Fill("12",event -> weight);
	    if (mass < massCut){
	      if (pt > 7) muonTrigsLoMass -> Fill("7",event -> weight);
	      if (pt > 8) muonTrigsLoMass -> Fill("8",event -> weight);
	      if (pt > 9) muonTrigsLoMass -> Fill("9",event -> weight);
	      if (pt > 12) muonTrigsLoMass -> Fill("12",event -> weight);
 
	    }
	    else{
	      if (pt > 7) muonTrigsHiMass -> Fill("7",event -> weight);
	      if (pt > 8) muonTrigsHiMass -> Fill("8",event -> weight);
	      if (pt > 9) muonTrigsHiMass -> Fill("9",event -> weight);
	      if (pt > 12) muonTrigsHiMass -> Fill("12",event -> weight);
	    }
	    }
	}
      }

      //Fill total column in all muon counting hists
      Mu1_NoPt -> Fill(0);
      Mu1_5GeV -> Fill(0);
      Mu2_NoPt -> Fill(0);
      Mu2_5GeV -> Fill(0);
      
      if(event -> allMuons.size() == 1){
	Mu1_NoPt -> Fill(1.1);
	if(event -> allMuons.at(0)->pt > 5) Mu1_5GeV -> Fill(1.1);
      }
      if(event -> allMuons.size() > 1){
	Mu1_NoPt -> Fill(1.1);
	Mu2_NoPt -> Fill(1.1);
	if(event -> allMuons.at(0)->pt > 5) Mu1_5GeV -> Fill(1.1);
	if(event -> allMuons.at(1)->pt > 5) Mu2_5GeV -> Fill(1.1);
      }
	
      if(event->doTrigEmulation){
	MC -> Fill("all_SR",event -> weightNoTrigger);
	MC -> Fill("SR_HLT_HT330_4j_75_60_45_40_3b",event -> weight);
	if(event -> truth -> m4b > massCut){
	  MC -> Fill("hiMass_SR", event -> weightNoTrigger);
	  MC -> Fill("hiMass_SR_HLT_HT330_4j_75_60_45_40_3b",event -> weight);
	}
	else{
	  MC -> Fill("loMass_SR", event -> weightNoTrigger);
	  MC -> Fill("loMass_SR_HLT_HT330_4j_75_60_45_40_3b",event -> weight);
	}
	BasicFill(cut+"_SR", event, event->weightNoTrigger);
	BasicFill(cut+"_SR_HLT_HT330_4j_75_60_45_40_3b", event, event->weight);
	BasicFill(cut+"_SR_HLT", event, event->weight);
      }
      else{
	BasicFill(cut+"_SR", event);
	//Cut+SR+Trigger
	if(event->passL1)                      BasicFill(cut+"_SR_L1", event);
	if(event->HLT_HT330_4j_75_60_45_40_3b){
	  BasicFill(cut+"_SR_HLT_HT330_4j_75_60_45_40_3b", event);
	}
	else{
	  double mass = event -> truth -> m4b;
	  if(mass < massCut){ 
	    muTrigs_LoMass_noMC     -> Fill("Total",event -> weight); 
	    muTrigs_LoMass_noMC_sip -> Fill("Total",event -> weight);
	  }
	  else{
	    muTrigs_HiMass_noMC     -> Fill("Total",event -> weight); 
	    muTrigs_HiMass_noMC_sip -> Fill("Total",event -> weight);
	  }
	  muTrigs_noMC     -> Fill("Total",event -> weight);
	  muTrigs_noMC_sip -> Fill("Total",event -> weight);
	  if(event -> allMuons.size() > 0){
	    double pt  = event -> allMuons.at(0) -> pt;
	    double sip = event -> allMuons.at(0) -> sip3d;
	    if (fabs(event -> allMuons.at(0) -> eta) < 1.5){
	      if (pt > 7){
		muTrigs_noMC -> Fill("7",event -> weight);
		if (sip > 4) muTrigs_noMC_sip -> Fill("7",event -> weight);
	      }
	      if (pt > 8){
		muTrigs_noMC -> Fill("8",event -> weight);
		if (sip > 5) muTrigs_noMC_sip -> Fill("8",event -> weight);
	      }
	      if (pt > 9){
		muTrigs_noMC -> Fill("9",event -> weight);
		if (sip > 5) muTrigs_noMC_sip -> Fill("9",event -> weight);
	      }
	      if (pt > 12){
		muTrigs_noMC -> Fill("12",event -> weight);
		if (sip > 6) muTrigs_noMC_sip -> Fill("12",event -> weight);
	      }
	      //	      std::cout<<event->HLT_HT330_4j_75_60_45_40_3b<<std::endl;
	      if (mass < massCut){
		if (pt > 7){
		  muTrigs_LoMass_noMC -> Fill("7",event -> weight);
		  if (sip > 4) muTrigs_LoMass_noMC_sip -> Fill("7",event -> weight);
		}
		if (pt > 8){
		  muTrigs_LoMass_noMC -> Fill("8",event -> weight);
		  if (sip > 5) muTrigs_LoMass_noMC_sip -> Fill("8",event -> weight);
		}
		if (pt > 9){
		  muTrigs_LoMass_noMC -> Fill("9",event -> weight);
		  if (sip > 5) muTrigs_LoMass_noMC_sip -> Fill("9",event -> weight);
		}
		if (pt > 12){
		  muTrigs_LoMass_noMC -> Fill("12",event -> weight);
		  if (sip > 6) muTrigs_LoMass_noMC_sip -> Fill("12",event -> weight);
		}
	      }
	      else{
		if (pt > 7){
		  muTrigs_HiMass_noMC     -> Fill("7",event -> weight);
		  if (sip > 4) muTrigs_HiMass_noMC_sip -> Fill("7",event -> weight);
		}
		if (pt > 8){
		  muTrigs_HiMass_noMC     -> Fill("8",event -> weight);
		  if (sip > 5) muTrigs_HiMass_noMC_sip -> Fill("8",event -> weight);
		}
		if (pt > 9){
		  muTrigs_HiMass_noMC     -> Fill("9",event -> weight);
		  if (sip > 5) muTrigs_HiMass_noMC_sip -> Fill("9",event -> weight);
		}
		if (pt > 12){
		  muTrigs_HiMass_noMC     -> Fill("12",event -> weight);
		  if (sip > 6) muTrigs_HiMass_noMC_sip -> Fill("12",event -> weight);
		}
	      }
	    }
	  }
	}

	if(event->HLT_4j_103_88_75_15_2b_VBF1) BasicFill(cut+"_SR_HLT_4j_103_88_75_15_2b_VBF1", event);
	if(event->HLT_4j_103_88_75_15_1b_VBF2) BasicFill(cut+"_SR_HLT_4j_103_88_75_15_1b_VBF2", event);
	if(event->HLT_2j116_dEta1p6_2b)        BasicFill(cut+"_SR_HLT_2j116_dEta1p6_2b", event);
	if(event->HLT_J330_m30_2b)             BasicFill(cut+"_SR_HLT_J330_m30_2b", event);
	if(event->HLT_j500)                    BasicFill(cut+"_SR_HLT_j500", event);
	if(event->HLT_2j300ave)                BasicFill(cut+"_SR_HLT_2j300ave", event);
	if(event->passHLT)                     BasicFill(cut+"_SR_HLT", event);
      }
    }
  }

  return;
}

void cutflowHists::labelsDeflate(){
  unitWeight->LabelsDeflate("X");
  //unitWeight->LabelsOption("a");
  weighted  ->LabelsDeflate("X");
  //weighted  ->LabelsOption("a");
  if(truthM4b != NULL){
    truthM4b->LabelsDeflate("Y");
    truthM4b->LabelsOption("a","Y");
  }
  return;  
}

cutflowHists::~cutflowHists(){} 

