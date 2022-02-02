#if !defined(dump_H)
#define dump_H

#include <string>
#include <vector>
#include <unordered_map>
#include <TROOT.h>
#include <TTree.h>
#include <TFile.h>

#define FUNDAMENTAL_TYPE_BRANCH(TYPE, FUNC, ARGS)\
switch (TYPE)\
{\
    case('B'):FUNC<Char_t>    ARGS;break;\
    case('b'):FUNC<UChar_t>   ARGS;break;\
    case('S'):FUNC<Short_t>   ARGS;break;\
    case('s'):FUNC<UShort_t>  ARGS;break;\
    case('I'):FUNC<Int_t>     ARGS;break;\
    case('i'):FUNC<UInt_t>    ARGS;break;\
    case('F'):FUNC<Float_t>   ARGS;break;\
    case('f'):FUNC<Float16_t> ARGS;break;\
    case('D'):FUNC<Double_t>  ARGS;break;\
    case('d'):FUNC<Double32_t>ARGS;break;\
    case('L'):FUNC<Long64_t>  ARGS;break;\
    case('l'):FUNC<ULong64_t> ARGS;break;\
    case('G'):FUNC<Long_t>    ARGS;break;\
    case('g'):FUNC<ULong_t>   ARGS;break;\
    case('O'):FUNC<Bool_t>    ARGS;break;\
    default:break;\
}

namespace nTupleAnalysis::dump{

class dumpBranch{
    public:
        std::string name;
        void* value;
        char type;
        dumpBranch(const std::string & _name, char _type)
        {
            name = _name;
            type = _type;
            FUNDAMENTAL_TYPE_BRANCH(type, init, ())
        }
        ~dumpBranch()
        {
            FUNDAMENTAL_TYPE_BRANCH(type, clean, ())
        }
        void fill(const auto &val)
        {
            FUNDAMENTAL_TYPE_BRANCH(type, set, (val))
        }
        const char* leafname();
    private:
        template<typename T> void init();
        template<typename T>
        void set(const auto &val)
        {
            *static_cast<T*>(value) = static_cast<T>(val);
        }
        template<typename T> void clean();
};

class dumpRoot{
    public:
        TFile *rootFile = nullptr;
        TTree *rootTree = nullptr;
        dumpRoot(const std::string &);
        void fill(const std::string & var, const auto & val)
        {
            if(variables.find(var) != variables.end())
            {
                variables[var]->fill(val);
            }
        }
        void fill();
        void close();
    private:
        std::unordered_map<std::string, std::shared_ptr<dumpBranch>> variables;
};

}

#undef FUNDAMENTAL_TYPE_BRANCH

#endif