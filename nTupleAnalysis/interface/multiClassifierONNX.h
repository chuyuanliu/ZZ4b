// -*- C++ -*-
#if SLC6 == 0
#if !defined(multiClassifierONNX_H)
#define multiClassifierONNX_H

#include <iostream>
#include "PhysicsTools/ONNXRuntime/interface/ONNXRuntime.h"
//#include "ZZ4b/nTupleAnalysis/interface/eventData.h"

//using namespace cms::Ort;

namespace nTupleAnalysis {
  class eventData;

  class multiClassifierONNX {
  public:

    multiClassifierONNX(std::string modelFile, bool _debug);
    
    std::unique_ptr<cms::Ort::ONNXRuntime> model;

    std::vector<std::string> input_names;
    std::vector<std::string> output_names;
    cms::Ort::FloatArrays input;
    cms::Ort::FloatArrays output;
    std::vector<float> c_score;
    std::vector<float> q_score;
    bool debug;

    void clear();
    void loadInput(eventData* event);
    void run();
    void run(eventData* event);
    void dump();
    
    ~multiClassifierONNX(); 

  };

}
#endif // multiClassifierONNX_H
#endif // SLC6
