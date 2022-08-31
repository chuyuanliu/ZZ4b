#include "ZZ4b/nTupleAnalysis/interface/massRegionHists.h"
#include "nTupleAnalysis/baseClasses/interface/helpers.h"

using namespace nTupleAnalysis;

massRegionHists::massRegionHists(std::string name, fwlite::TFileService& fs, bool isMC, bool _blind, std::string histDetailLevel, bool _debug, eventData* event) {
  if(_debug) std::cout << "massRegionHists::massRegionHists(std::string name, fwlite::TFileService& fs, bool isMC, bool _blind, std::string histDetailLevel, bool _debug, eventData* event)" << std::endl;
  dir = fs.mkdir(name);
  blind = _blind;
  debug = _debug;

  if(nTupleAnalysis::findSubStr(histDetailLevel,"Inclusive")){
    inclusive = new viewHists(name+"/inclusive", fs, isMC, debug, NULL, histDetailLevel);
  }
  if(nTupleAnalysis::findSubStr(histDetailLevel,"SB")){
    SB        = new viewHists(name+"/SB", fs, isMC, debug, event, histDetailLevel);
  }

  if(nTupleAnalysis::findSubStr(histDetailLevel,"HHSR")){
    HHSR      = new viewHists(name+"/HHSR",      fs, isMC, debug, event, histDetailLevel );
  }

  if(nTupleAnalysis::findSubStr(histDetailLevel,"TTCR")){
    TTCR      = new viewHists(name+"/TTCR",      fs, isMC, debug, event, histDetailLevel );
  }
  
  if(HHSR) std::cout << "\t Turning on HHSR " << std::endl;

} 

void massRegionHists::Fill(eventData* event, std::shared_ptr<eventView> &view){
  if(blind && (view->SR)) return;
  
  if(inclusive) inclusive->Fill(event, view);//, nViews, nViews_10, nViews_11, nViews_12);
  if(SB && view->SB) SB->Fill(event, view);//, nViews, nViews_10, nViews_11, nViews_12);
  if(HHSR && view->HHSR) HHSR->Fill(event, view);//, nViews, nViews_10, nViews_11, nViews_12);

  if(TTCR && event->passTTCR) TTCR->Fill(event, view);
  return;
}

massRegionHists::~massRegionHists(){} 


