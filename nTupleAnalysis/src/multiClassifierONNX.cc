#if SLC6 == 0 //Defined in ZZ4b/nTupleAnalysis/BuildFile.xml
#include "ZZ4b/nTupleAnalysis/interface/multiClassifierONNX.h"
#include "ZZ4b/nTupleAnalysis/interface/eventData.h"
#include "ZZ4b/nTupleAnalysis/interface/utils.h"

using namespace nTupleAnalysis;

multiClassifierONNX::multiClassifierONNX(std::string modelFile, bool _debug) {
  debug = _debug;
  Ort::SessionOptions* session_options = new Ort::SessionOptions();
  session_options->SetIntraOpNumThreads(1);

  if(modelFile.find("/*offset*/") == std::string::npos){
    models.push_back(std::move(std::make_unique<cms::Ort::ONNXRuntime>(modelFile, session_options)));
    std::cout << "loaded model " << modelFile << std::endl;
    models[0]->getOutputNames();
  }
  else{
    for(int i = 0; i < 3; ++i){
      auto modelFileName = utils::fillString(modelFile, {{"offset", std::to_string(i)}});
      models.push_back(std::move(std::make_unique<cms::Ort::ONNXRuntime>(modelFileName, session_options)));
      std::cout << "loaded model " << modelFileName << std::endl;
    }
  }


  input_names = {"J","O","A"};
  output_names= {"c_logits", "q_logits"};

  this->clear();

  // canJets
  input.emplace_back(4*4,1);

  // othJets
  input.emplace_back(5*8,-1);
  
  // ancillary features
  input.emplace_back(4,1);

  this->run();
  this->dump();

} 

void multiClassifierONNX::clear(){
  if(debug) std::cout << "multiClassifierONNX::clear()" << std::endl;
}

void multiClassifierONNX::loadInput(eventData* event){
  if(debug) std::cout << "multiClassifierONNX::loadInput()" << std::endl;
  // canJets
  for(uint i = 0; i < 4; i++){
    input[0][   i] = event->canJets[i]->pt;
    input[0][4+i] = event->canJets[i]->eta;
    input[0][8+i] = event->canJets[i]->phi;
    input[0][12+i] = event->canJets[i]->m;
  };

  // othJets
  for(uint i = 0; i < event->nAllNotCanJets && i < 8; i++){
    input[1][   i] = event->allNotCanJets[i]->pt;
    input[1][8+i]  = event->allNotCanJets[i]->eta;
    input[1][16+i] = event->allNotCanJets[i]->phi;
    input[1][24+i] = event->allNotCanJets[i]->m;
    bool isSelJet = (event->allNotCanJets[i]->pt>40) & (fabs(event->allNotCanJets[i]->eta)<2.4);
    input[1][32+i] = isSelJet ? 1 : 0; 
  };
  for(uint i =  event->nAllNotCanJets; i < 8; i++){
    input[1][   i] = -1;
    input[1][8+i]  = -1;
    input[1][16+i] = -1;
    input[1][24+i] = -1;
    input[1][32+i] = -1; 
  };

  // ancillary features
  input[2][0] = event->year - 2010;
  input[2][1] = event->nSelJets;
  input[2][2] = event->xW;
  input[2][3] = event->xbW;

  offset = event->event % models.size();

}

void multiClassifierONNX::run(){
  if(debug) std::cout << "multiClassifierONNX::run()" << std::endl;
  output = models[offset]->run(input_names, input, output_names, 1);
  c_score = output[0];
  q_score = output[1];
}

void multiClassifierONNX::run(eventData* event){
  this->clear();
  this->loadInput(event);
  this->run();
}

void multiClassifierONNX::dump(){
  std::cout << "multiClassifierONNX::dump() inputs" << std::endl;
  for(std::vector<float>::size_type i=0; i<input.size(); i++){
    std::cout << input_names[i] << ": ";
    for(std::vector<float>::size_type j=0; j<input[i].size(); j++){
      std::cout << input[i][j] << " ";
    }
    std::cout << std::endl;
  };
  std::cout << "multiClassifierONNX::dump() outputs" << std::endl;
  for(std::vector<float>::size_type i=0; i<output.size(); i++){
    std::cout << output_names[i] << ": ";
    for(std::vector<float>::size_type j=0; j<output[i].size(); j++){
      std::cout << output[i][j] << " ";
    }
    std::cout << std::endl;
  };
}

multiClassifierONNX::~multiClassifierONNX(){} 

#endif
