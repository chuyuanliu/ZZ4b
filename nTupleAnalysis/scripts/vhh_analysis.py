from fileinput import filename
import time
from copy import copy
import textwrap
import os, re, shutil
import sys
import subprocess
import shlex
from glob import glob
import optparse
from threading import Thread
sys.path.insert(0, 'nTupleAnalysis/python/') #https://github.com/patrickbryant/nTupleAnalysis
from commandLineHelpers import *
import vhh_fileHelper as fh

class nameTitle:
    def __init__(self, name, title):
        self.name  = name
        self.title = title

CMSSW = getCMSSW()
USER = getUSER()
EOSOUTDIR = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/VHH/"
CONDOROUTPUTBASE = "/store/user/"+USER+"/condor/VHH/"
TARBALL   = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/"+CMSSW+".tgz"


parser = optparse.OptionParser()
parser.add_option('--makeFileList',action="store_true",                        default=False, help="Make file list with DAS queries")
parser.add_option('-e',            action="store_true", dest="execute",        default=False, help="Execute commands. Default is to just print them")
parser.add_option('-s',            action="store_true", dest="doSignal",       default=False, help="Run signal MC")
parser.add_option('-t',            action="store_true", dest="doTT",           default=False, help="Run ttbar MC")
parser.add_option('-a',            action="store_true", dest="doAccxEff",      default=False, help="Make Acceptance X Efficiency plots")
parser.add_option('-d',            action="store_true", dest="doData",         default=False, help="Run data")
parser.add_option('-q',            action="store_true", dest="doQCD",          default=False, help="Subtract ttbar MC from data to make QCD template")
parser.add_option('-y',                                 dest="year",           default="2016,2017,2018", help="Year or comma separated list of years")
parser.add_option('-o',                                 dest="outputBase",     default="/uscms/home/"+USER+"/nobackup/VHH/", help="path to output")
parser.add_option('-w',            action="store_true", dest="doWeights",      default=False, help="Fit jetCombinatoricModel and nJetClassifier TSpline")
parser.add_option('--makeJECSyst', action="store_true", dest="makeJECSyst",    default=False, help="Make jet energy correction systematics friend TTrees")
parser.add_option('--doJECSyst',   action="store_true", dest="doJECSyst",      default=False, help="Run event loop for jet energy correction systematics")
parser.add_option('-j',            action="store_true", dest="useJetCombinatoricModel",       default=False, help="Use the jet combinatoric model")
parser.add_option('--JCM',         action="store_true", dest="storeJetCombinatoricModel",       default=False, help="Use the jet combinatoric model")
parser.add_option('-r',            action="store_true", dest="reweight",       default=False, help="Do reweighting with nJetClassifier TSpline")
parser.add_option('--bTagSyst',    action="store_true", dest="bTagSyst",       default=False, help="run btagging systematics")
parser.add_option('--puIdSyst',    action="store_true", dest="puIdSyst",       default=False, help="run PU jet ID systematics")
parser.add_option('--plot',        action="store_true", dest="doPlots",        default=False, help="Make Plots")
parser.add_option('-p', '--createPicoAOD',              dest="createPicoAOD",  type="string", help="Create picoAOD with given name")
parser.add_option(      '--root2h5',                    dest="root2h5",        default=False, action="store_true", help="convert picoAOD.h5 to .root")
parser.add_option(      '--xrdcph5',                    dest="xrdcph5",        default="", help="copy .h5 files to EOS if toEOS else download from EOS")
parser.add_option(      '--h52root',                    dest="h52root",        default=False, action="store_true", help="convert picoAOD.root to .h5")
parser.add_option('-f', '--fastSkim',                   dest="fastSkim",       action="store_true", default=False, help="Do fast picoAOD skim")
parser.add_option(      '--looseSkim',                  dest="looseSkim",      action="store_true", default=False, help="Relax preselection to make picoAODs for JEC Uncertainties which can vary jet pt by a few percent.")
parser.add_option('-n', '--nevents',                    dest="nevents",        default="-1", help="Number of events to process. Default -1 for no limit.")
parser.add_option(      '--detailLevel',                dest="detailLevel",  default="allEvents.passMV.SB.HHSR.fourTag.threeTag.bdtStudy", help="Histogramming detail level. ")
parser.add_option('-c', '--makeCombineHist',    action="store_true", dest="makeCombineHist",      default=False, help="Make CombineTool input hists")
parser.add_option(   '--loadHemisphereLibrary',    action="store_true", default=False, help="load Hemisphere library")
parser.add_option(   '--noDiJetMassCutInPicoAOD',    action="store_true", default=False, help="create Output Hemisphere library")
parser.add_option(   '--createHemisphereLibrary',    action="store_true", default=False, help="create Output Hemisphere library")
parser.add_option(   '--maxNHemis',    default=10000, help="Max nHemis to load")
parser.add_option(   '--inputHLib3Tag', default='$PWD/data18/hemiSphereLib_3TagEvents_*root',          help="Base path for storing output histograms and picoAOD")
parser.add_option(   '--inputHLib4Tag', default='$PWD/data18/hemiSphereLib_4TagEvents_*root',           help="Base path for storing output histograms and picoAOD")
parser.add_option(   '--SvB_ONNX', action="store_true", default=False,           help="Run ONNX version of SvB model. Model path specified in analysis.py script")
parser.add_option(   '--condor',   action="store_true", default=False,           help="Run on condor")
parser.add_option(   '--trigger', action="store_true", default=False, help = 'do trigger emulation')
parser.add_option(   '--friends', dest = 'friends',default='FvT_Nominal,SvB_MA_VHH_8nc', help = 'friend root files')
# for VHH study
parser.add_option(   '--coupling ', dest = 'coupling', default = ',CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0,C3:20_0', help = 'set signal coupling')
parser.add_option(   '--higherOrder',    action="store_true", default=False, help="reweight signal MC to NNLO for ZHH or NLO for WHH")
parser.add_option(   '--ttbarProcesses', dest = 'ttbarProcesses', default = 'TTToHadronic,TTToSemiLeptonic,TTTo2L2Nu', help = 'select ttbar processes')
parser.add_option(   '--separate3b4b', dest = 'separate3b4b', action="store_true", default=False, help = 'run 4b, 3b separately')
parser.add_option(   '--debug', dest = 'debug', action="store_true", default=False, help = 'enable debug mode')
parser.add_option(   '--extraOutput', dest = 'extraOutput', action="store_true", default=False, help = 'make extra root file')
parser.add_option(   '--histsTag', dest = 'histsTag', default='', help = 'extra tags in hists.root filename')
parser.add_option(   '--runKlBdt', dest = 'runKlBdt', action="store_true", default=False, help = 'run kl BDT')
parser.add_option(   '--calcPuIdSF', dest = 'calcPuIdSF', action="store_true", default=False, help = 'calculate PU jet ID SF')
parser.add_option(   '--applyPuIdSF', dest = 'applyPuIdSF', action="store_true", default=False, help = 'apply PU jet ID SF')
parser.add_option(   '--nTags', dest = 'nTags', default='_4b', help = 'run on n tag events for ttbar')

o, a = parser.parse_args()

fromNANOAOD = (o.createPicoAOD == "picoAOD.root" or o.createPicoAOD == "none") 
if o.fastSkim and fromNANOAOD:
    EOSOUTDIR = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/skims/"

#
# Analysis in several "easy" steps
#

### 1. Jet Combinatoric Model
# First run on data and ttbar MC
# > python ZZ4b/nTupleAnalysis/scripts/analysis.py -d -t -q -y 2016,2017,2018 -e
# Then make jet combinatoric model 
# > python ZZ4b/nTupleAnalysis/scripts/analysis.py -w -y 2016,2017,2018 -e
# Now run again and update the automatically generated picoAOD by making a temporary one which will then be copied over picoAOD.root
# > python ZZ4b/nTupleAnalysis/scripts/analysis.py -d -t -q -y 2016,2017,2018 -j -p tempPicoAOD.root -e

### 2. ThreeTag to FourTag reweighting
# Now convert the picoAOD to hdf5 to train the Four Vs Three tag classifier (FvT)
# > python ZZ4b/nTupleAnalysis/scripts/convert_root2h5.py -i "/uscms/home/bryantp/nobackup/ZZ4b/data201*/picoAOD.root /uscms/home/bryantp/nobackup/ZZ4b/TTTo*201*/picoAOD.root /uscms/home/bryantp/nobackup/ZZ4b/*Z*201*/picoAOD.root"
# Now train the classifier
# > python ZZ4b/nTupleAnalysis/scripts/multiClassifier.py -c FvT -d "/uscms/home/bryantp/nobackup/ZZ4b/data201*/picoAOD.h5" -t "/uscms/home/bryantp/nobackup/ZZ4b/TTTo*201*/picoAOD.h5"
# Take the best result and update the hdf5 files with classifier output for each event
# > python ZZ4b/nTupleAnalysis/scripts/multiClassifier.py -c FvT -d "/uscms/home/bryantp/nobackup/ZZ4b/data201*/picoAOD.h5" -t "/uscms/home/bryantp/nobackup/ZZ4b/TTTo*201*/picoAOD.h5" -s "/uscms/home/bryantp/nobackup/ZZ4b/*Z*201*/picoAOD.h5" -m <FvT_model.pkl> -u

### 3. Signal vs Background Classification
# Train the classifier
# > python ZZ4b/nTupleAnalysis/scripts/multiClassifier.py -c SvB -d "/uscms/home/bryantp/nobackup/ZZ4b/data2018*/picoAOD.h5" -t "/uscms/home/bryantp/nobackup/ZZ4b/TTTo*201*/picoAOD.h5" -s "/uscms/home/bryantp/nobackup/ZZ4b/*ZH2018/picoAOD.h5"
# Update the hdf5 files with the classifier output
# > python ZZ4b/nTupleAnalysis/scripts/multiClassifier.py -c SvB -d "/uscms/home/bryantp/nobackup/ZZ4b/data2018*/picoAOD.h5" -t "/uscms/home/bryantp/nobackup/ZZ4b/TTTo*201*/picoAOD.h5" -s "/uscms/home/bryantp/nobackup/ZZ4b/*ZH2018/picoAOD.h5" -m <SvB_model.pkl> -u
# Update the picoAOD.root with the results of the trained classifiers
# > python ZZ4b/nTupleAnalysis/scripts/convert_h52root.py -i "/uscms/home/bryantp/nobackup/ZZ4b/data201*/picoAOD.h5 /uscms/home/bryantp/nobackup/ZZ4b/TTTo*201*/picoAOD.h5 /uscms/home/bryantp/nobackup/ZZ4b/*Z*201*/picoAOD.h5"
# Now run the Event Loop again to make the reweighted histograms with the classifier outputs
# > python ZZ4b/nTupleAnalysis/scripts/analysis.py    -d -t -q -y 2016,2017,2018 -j    -e  (before reweighting)
# > python ZZ4b/nTupleAnalysis/scripts/analysis.py -s -d -t    -y 2016,2017,2018 -j -r -e   (after reweighting)

### 4. Make plots
# > python ZZ4b/nTupleAnalysis/scripts/analysis.py --plot -y 2016,2017,2018,RunII -j -e    (before reweighting)
# > python ZZ4b/nTupleAnalysis/scripts/analysis.py --plot -y 2016,2017,2018,RunII -j -r -e  (after reweighting)
# To make acceptance X efficiency plots first you need the cutflows without the loosened jet preselection needed for the JEC variations. -a will then make the accXEff plot input hists and make the nice .pdf's:
# > python ZZ4b/nTupleAnalysis/scripts/analysis.py -s  -y 2016,2017,2018 -p none -a -e

### 5. Jet Energy Correction Uncertainties!
# Make JEC variation friend TTrees with
# > python ZZ4b/nTupleAnalysis/scripts/analysis.py --makeJECSyst -y 2018 -e
# Need to make onnx SvB model to run in CMSSW on JEC variations
# In mlenv5 on cmslpcgpu node run
# > python ZZ4b/nTupleAnalysis/scripts/multiClassifier.py -c SvB -m <model.pkl>
# Copy the onnx file to an sl7 CMSSW_11 area
# Specify the model.onnx above in the python variable SvB_ONNX
# Run signal samples with --SvB_ONNX --doJECSyst in sl7 and CMSSW_11

# Condor
# tar -zcvf CMSSW_11_1_0_pre5.tgz CMSSW_11_1_0_pre5 --exclude="*.pdf" --exclude=".git" --exclude="PlotTools" --exclude="madgraph" --exclude="*.pkl" --exclude="*.root" --exclude="tmp" --exclude="combine" --exclude-vcs --exclude-caches-all; ls -alh
# xrdfs root://cmseos.fnal.gov/ rm /store/user/bryantp/CMSSW_11_1_0_pre5.tgz
# xrdcp -f CMSSW_11_1_0_pre5.tgz root://cmseos.fnal.gov//store/user/bryantp/CMSSW_11_1_0_pre5.tgz


#
# Config
#
nWorkers   = 3
script     = "ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py"
years      = o.year.split(",")
eras   = copy(years)
if '2016' in eras:
    eras.remove('2016')
    eras += ['2016_preVFP', '2016_postVFP']
ttbarProcesses = o.ttbarProcesses.split(',')
lumiDict   = {'2016':  '36.3e3',#35.8791
              '2016_preVFP': '19.5e3',
              '2016_postVFP': '16.5e3',
              '2017':  '36.7e3',#36.7338
              '2018':  '59.8e3',#59.9656
              '17+18': '96.7e3',
              'RunII':'132.8e3',
              }
bTagDict   = {"2016": "0.6",#"0.3093", #https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation2016Legacy
              "2017": "0.6",#"0.3033", #https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation94X
              "2018": "0.6",#"0.2770"} #https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X
              }
outputBase = o.outputBase
gitRepoBase= 'ZZ4b/nTupleAnalysis/weights/'

# File lists
periods = {"2016": "BCDEFGH",
           "2017": "CDEF",
           "2018": "ABCD"}

JECSystList = ["_jerUp", "_jerDown",
               "_jesTotalUp", "_jesTotalDown"]

# VHH Files
if o.coupling == 'None':
    couplings = []
else:
    couplings = fh.getCouplingList(o.coupling)

def dataFiles(year):
    if fromNANOAOD:
        files = []
        for period in periods[year]:
            files += glob('ZZ4b/fileLists/data%s%s_chunk*.txt'%(year,period))
        return files
    elif o.separate3b4b:
        return ["closureTests/ULTrig/fileLists/data" + year + tag + ".txt " for tag in ['_3b', '_4b']]
    else:
        return ["ZZ4b/fileLists/data" + year + period + ".txt" for period in periods[year]]

# Jet Combinatoric Model
JCMRegion = "SB"
JCMVersion = "00-00-02"
JCMCut = "passNjOth"
def jetCombinatoricModel(year):
    #return gitRepoBase+"data"+year+"/jetCombinatoricModel_"+JCMRegion+"_"+JCMVersion+".txt"
    return gitRepoBase+"dataRunII/jetCombinatoricModel_"+JCMRegion+"_"+JCMVersion+".txt"
#reweight = gitRepoBase+"data"+year+"/reweight_"+JCMRegion+"_"+JCMVersion+".root"

SvB_ONNX = "ZZ4b/nTupleAnalysis/pytorchModels/SvB_MA_VHH/SvB_MA_HCR+attention_8_np1052_seed0_lr0.01_epochs20_offset/*offset*/_epoch20.onnx"

def signalFiles(signals, year):
    if year == '2016':
        files = []
        for signalYear in ['2016_preVFP', '2016_postVFP']:
            files += ["ZZ4b/fileLists/" + signal + signalYear + ".txt" for signal in signals]
        return files
    else:
        return ["ZZ4b/fileLists/" + signal + year + ".txt" for signal in signals]

def ttbarFiles(year):
    if fromNANOAOD:
        files = []
        for process in ttbarProcesses:
            files+= glob('ZZ4b/fileLists/%s%s*_chunk*.txt'%(process, year))
        return files
    elif o.separate3b4b:
        ttYears = [year]
        if year == '2016':
            ttYears = ['2016_preVFP', '2016_postVFP']
        return ['closureTests/ULTrig/fileLists/' + process + ttYear + tag + '.txt' for process in ttbarProcesses for ttYear in ttYears for tag in o.nTags.split(',')]
    else:
        return ['ZZ4b/fileLists/' + process + year + '.txt' for process in ttbarProcesses]

def accxEffFiles(signals, year):
    return [outputBase + signal + year + "/hists.root" for signal in signals]
DAG = None
if o.condor:
    DAG = dag(fileName="analysis.dag")

def makeJECSyst():
    basePath = EOSOUTDIR if o.condor else outputBase
    cmds=[]
    for signals in couplings:
        for year in eras:
            for process in signals[:2]:
                cmd  = 'python PhysicsTools/NanoAODTools/scripts/nano_postproc.py '
                cmd += basePath+process+year+'/ '
                cmd += basePath+process+year+'/picoAOD.root '
                cmd += '--friend '
                cmd += '-I nTupleAnalysis.baseClasses.jetmetCorrectors jetmetCorrectorUL'+year # modules are defined in https://github.com/patrickbryant/nTupleAnalysis/blob/master/baseClasses/python/jetmetCorrectors.py
                cmds.append(cmd)

    execute(cmds, o.execute, condor_dag=DAG)

def makeTARBALL():
    base="/uscms/home/"+USER+"/nobackup/"
    if os.path.exists(base+CMSSW+".tgz"):
        print "# TARBALL already exists, skip making it"
        return
    cmd  = 'tar -C '+base+' -zcvf '+base+CMSSW+'.tgz '+CMSSW
    cmd += ' --exclude="*.pdf" --exclude="*.jdl" --exclude="*.stdout" --exclude="*.stderr" --exclude="*.log"'
    cmd += ' --exclude=".git" --exclude="PlotTools" --exclude="madgraph" --exclude="*.pkl"'# --exclude="*.root"'#some root files needed for nano_postproc.py jetmetCorrector
    cmd += ' --exclude="toy4b"'
    cmd += ' --exclude="CombineHarvester"'
    cmd += ' --exclude="HiggsAnalysis"'
    cmd += ' --exclude="closureFits"'
    cmd += ' --exclude="higgsCombine*.root"'
    cmd += ' --exclude="tmp" --exclude="combine" --exclude-vcs --exclude-caches-all'
    execute(cmd, o.execute)
    cmd  = 'ls '+base+' -alh'
    execute(cmd, o.execute)
    cmd = "xrdfs root://cmseos.fnal.gov/ mkdir /store/user/"+USER+"/condor"
    execute(cmd, o.execute)
    cmd = "xrdcp -f "+base+CMSSW+".tgz "+TARBALL
    execute(cmd, o.execute)
    

def doSignal():
    basePath = EOSOUTDIR if o.condor else outputBase
    cp = 'xrdcp -f ' if o.condor else 'cp '

    mkdir(basePath, o.execute)

    cmds=[]
    JECSysts = [""]
    if o.doJECSyst: 
        JECSysts = JECSystList

    for JECSyst in JECSysts:
        histFile = "hists"+JECSyst+o.histsTag+".root"
        if o.createPicoAOD == "picoAOD.root" or o.createPicoAOD == "none": histFile = "histsFromNanoAOD"+JECSyst+".root"
        
        for signals in couplings:
            for year in years:
                for fileList in signalFiles(signals[0:2],year):
                    era = year
                    if '2016' in fileList:
                        if '2016_preVFP' in fileList:
                            era = '2016_preVFP'
                        elif '2016_postVFP' in fileList: 
                            era = '2016_postVFP'
                    lumi = lumiDict[era]
                    cmd  = "nTupleAnalysis "+script
                    cmd += " -i "+fileList
                    cmd += " -o "+basePath
                    cmd += " -y "+year
                    cmd += " --era "+era
                    cmd += " -l "+lumi
                    cmd += " --histDetailLevel "+o.detailLevel
                    cmd += " --histFile "+histFile
                    cmd += " -p "+o.createPicoAOD if o.createPicoAOD else ""
                    cmd += " --runKlBdt " if o.runKlBdt or o.createPicoAOD else ""
                    #cmd += " -f " if o.fastSkim else ""
                    cmd += " --isMC"
                    cmd += " --doTrigEmulation" if o.trigger else ""
                    cmd += " --doHigherOrderReweight" if o.higherOrder else ""
                    cmd += " --bTag "+bTagDict[year]
                    cmd += " --bTagSF"
                    cmd += " --puIdSF" if o.applyPuIdSF else ""
                    cmd += " --bTagSyst" if o.bTagSyst else ""
                    cmd += " --puIdSyst" if o.puIdSyst else ""
                    cmd += " --nevents "+o.nevents
                    cmd += " --looseSkim" if (o.createPicoAOD or o.looseSkim) else "" # For signal samples we always want the picoAOD to be loose skim
                    cmd += " --SvB_ONNX "+SvB_ONNX if o.SvB_ONNX or o.doJECSyst else ""
                    cmd += " --JECSyst "+JECSyst if JECSyst else ""
                    cmd += " --friends " + o.friends if o.friends else ""
                    cmd += " --debug" if o.debug else ""
                    cmd += " --extraOutput bosonKinematics" if o.extraOutput else ""
                    # if o.createPicoAOD and o.createPicoAOD != "none":
                    #     if o.createPicoAOD != "picoAOD.root":
                    #         sample = fileList.split("/")[-1].replace(".txt","")
                    #         cmd += ' ; '+cp+basePath+sample+"/"+o.createPicoAOD+" "+basePath+sample+"/picoAOD.root"

                    cmds.append(cmd)

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)

    # cmds = []

    # for JECSyst in JECSysts:
    #     histFile = "hists"+JECSyst+".root" #+("_j" if o.useJetCombinatoricModel else "")+("_r" if o.reweight else "")+".root"
    #     if o.createPicoAOD == "picoAOD.root" or o.createPicoAOD == "none": histFile = "histsFromNanoAOD"+JECSyst+".root"
    #     for signals in couplings:
    #         for year in years:
    #             mkdir(basePath + signals[2] + year + "/", o.execute)
    #             cmd = "hadd -f"
    #             for i in [2,1,0]:
    #                 cmd += " " + basePath + signals[i] + year + "/" + histFile

    #                 cmds.append(cmd)

    # if o.condor: 
    #     DAG.addGeneration()
    # execute(cmds, o.execute, condor_dag=DAG)

    # cmds = []
    # if "2017" in years and "2018" in years:
    #     for JECSyst in JECSysts:
    #         histFile = "hists"+JECSyst+".root" #+("_j" if o.useJetCombinatoricModel else "")+("_r" if o.reweight else "")+".root"
    #         if o.createPicoAOD == "picoAOD.root" or o.createPicoAOD == "none": histFile = "histsFromNanoAOD"+JECSyst+".root"
    #         for signals in couplings:
    #             for sample in signals[0:3]:
    #                 mkdir(basePath + sample + "17+18/", o.execute)
    #                 cmd = "hadd -f"
    #                 for year in ["17+18", "2017", "2018"]:
    #                     cmd += " " + basePath + sample + year + "/" + histFile
    #                     cmds.append(cmd)
                
    # if o.condor:
    #     DAG.addGeneration()
    # execute(cmds, o.execute, condor_dag=DAG)

      
def doAccxEff():   
    cmds = []

    plotYears = copy(years)
    if "2017" in years and "2018" in years:
        plotYears += ["17+18"]

    for signals in couplings:
        for year in plotYears:
            for signal in accxEffFiles(signals[0:3], year):
                cmd = "python ZZ4b/nTupleAnalysis/scripts/vhh_makeAccxEff.py -i "+signal
                cmds.append(cmd)
    babySit(cmds, o.execute, maxJobs=nWorkers)

def doDataTT():
    basePath = EOSOUTDIR if o.condor else outputBase
    cp = 'xrdcp -f ' if o.condor else 'cp '

    mkdir(basePath, o.execute)

    # run event loop
    cmds=[]
    histFile = "hists"+("_j" if o.useJetCombinatoricModel else "")+("_r" if o.reweight else "")+o.histsTag+".root"
    if o.createPicoAOD == "picoAOD.root": histFile = "histsFromNanoAOD.root"

    for year in years:
        files = []
        if o.doData: files += dataFiles(year)
        if o.doTT:   files += ttbarFiles(year)
        for fileList in files:
            era = year
            if '2016' in fileList:
                if '2016_preVFP' in fileList:
                    era = '2016_preVFP'
                elif '2016_postVFP' in fileList: 
                    era = '2016_postVFP'
            lumi = lumiDict[era]
            cmd  = "nTupleAnalysis "+script
            cmd += " -i "+fileList
            cmd += " -o "+basePath
            cmd += " -y "+year
            cmd += " --era "+era
            cmd += " --histDetailLevel "+o.detailLevel
            cmd += " --histFile "+histFile
            cmd += " -j "+jetCombinatoricModel(year) if o.storeJetCombinatoricModel else ""
            cmd += " -r " if o.reweight else ""
            cmd += " -p "+o.createPicoAOD if o.createPicoAOD else ""
            cmd += " --runKlBdt " if o.runKlBdt or o.createPicoAOD else ""
            cmd += " -f " if o.fastSkim else ""
            cmd += " --bTag "+bTagDict[year]
            cmd += " --nevents "+o.nevents
            cmd += " --jcmNameLoad Nominal" if o.useJetCombinatoricModel else ""
            cmd += " --FvTName FvT_Nominal"
            cmd += (" --friends " + o.friends) if o.friends else ""
            cmd += " --debug" if o.debug else ""
            cmd += " --extraOutput bosonKinematics" if o.extraOutput else ""
            cmd += " --calcPuIdSF " if o.calcPuIdSF else ""
            if fileList in ttbarFiles(year):
                cmd += " -l "+lumi
                cmd += " --bTagSF"
                cmd += " --puIdSF" if o.applyPuIdSF else ""
                cmd += " --bTagSyst" if o.bTagSyst else ""
                cmd += " --isMC "
                cmd += " --doTrigEmulation" if o.trigger else ""
            if o.createHemisphereLibrary  and fileList not in ttbarFiles:
                cmd += " --createHemisphereLibrary "
            if o.noDiJetMassCutInPicoAOD:
                cmd += " --noDiJetMassCutInPicoAOD "
            if o.loadHemisphereLibrary:
                cmd += " --loadHemisphereLibrary "
                cmd += " --inputHLib3Tag "+o.inputHLib3Tag
                cmd += " --inputHLib4Tag "+o.inputHLib4Tag
            cmd += " --SvB_ONNX "+SvB_ONNX if o.SvB_ONNX else ""

            # if o.createPicoAOD and o.createPicoAOD != "none":
            #     if o.createPicoAOD != "picoAOD.root":
            #         sample = fileList.split("/")[-1].replace(".txt","")
            #         cmd += ' ; '+cp+basePath+sample+"/"+o.createPicoAOD+" "+basePath+sample+"/picoAOD.root"
            
            cmds.append(cmd)

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)

    # combine chunked picoAODs if we just skimmed them from the NANOAODs
    cmds = []
    if o.createPicoAOD == 'picoAOD.root' and fromNANOAOD:
        for year in years:
            if o.doData:
                for period in periods[year]:
                    cmd  = 'hadd -f %sdata%s%s/picoAOD.root'%(basePath, year, period)
                    nChunks = len(glob('ZZ4b/fileLists/data%s%s_chunk*.txt'%(year,period)))
                    for chunk in range(1,nChunks+1):
                        cmd += ' %sdata%s%s_chunk%02d/picoAOD.root '%(basePath, year, period, chunk)
                    cmds.append(cmd)

                    cmd  = 'hadd -f %sdata%s%s/histsFromNanoAOD.root'%(basePath, year, period)
                    for chunk in range(1,nChunks+1):
                        cmd += ' %sdata%s%s_chunk%02d/histsFromNanoAOD.root '%(basePath, year, period, chunk)
                    cmds.append(cmd)

            if o.doTT:
                # if year == '2016': 
                #     processes = [p+'_preVFP' for p in processes] + [p+'_postVFP' for p in processes]
                for process in ttbarProcesses:
                    cmd  = 'hadd -f %s%s%s/picoAOD.root'%(basePath, process, year)
                    nChunks = len(glob('ZZ4b/fileLists/%s%s_chunk*.txt'%(process, year)))
                    for chunk in range(1,nChunks+1):
                        cmd += ' %s%s%s_chunk%02d/picoAOD.root'%(basePath, process, year, chunk)
                    cmds.append(cmd)

                    cmd  = 'hadd -f %s%s%s/histsFromNanoAOD.root'%(basePath, process, year)
                    for chunk in range(1,nChunks+1):
                        cmd += ' %s%s%s_chunk%02d/histsFromNanoAOD.root'%(basePath, process, year, chunk)
                    cmds.append(cmd)

        if o.condor:
            DAG.addGeneration()
        execute(cmds, o.execute, condor_dag=DAG)
        return


    # make combined histograms for plotting purposes
    # cmds = []
    # for year in years:
    #     if o.doData:
    #         mkdir(basePath+"data"+year, o.execute)
    #         cmd = "hadd -f "+basePath+"data"+year+"/"+histFile+" "+" ".join([basePath+"data"+year+period+"/"+histFile for period in periods[year]])
    #         cmds.append(cmd)
    
    #     if o.doTT:
    #         files = ttbarFiles(year)
    #         if "ZZ4b/fileLists/TTToHadronic"+year+".txt" in files and "ZZ4b/fileLists/TTToSemiLeptonic"+year+".txt" in files and "ZZ4b/fileLists/TTTo2L2Nu"+year+".txt" in files:
    #             mkdir(basePath+"TT"+year, o.execute)
    #             cmd = "hadd -f "+basePath+"TT"+year+"/"+histFile+" "+basePath+"TTToHadronic"+year+"/"+histFile+" "+basePath+"TTToSemiLeptonic"+year+"/"+histFile+" "+basePath+"TTTo2L2Nu"+year+"/"+histFile
    #             cmds.append(cmd)

    # if o.condor:
    #     DAG.addGeneration()
    # execute(cmds, o.execute, condor_dag=DAG)

    # cmds = []
    # if "2017" in years and "2018" in years and "2016" in years:
    #     samples = []
    #     if o.doData: samples.append('data')
    #     if o.doTT: samples.append('TT')
    #     for sample in samples:
    #         mkdir(basePath + sample + "RunII/", o.execute)
    #         cmd = "hadd -f"
    #         for year in ["RunII", "2016", "2017", "2018"]:
    #             cmd += " " + basePath + sample + year + "/" + histFile
    #             cmds.append(cmd)
    # elif "2017" in years and "2018" in years:
    #     samples = []
    #     if o.doData: samples.append('data')
    #     if o.doTT: samples.append('TT')
    #     for sample in samples:
    #         mkdir(basePath + sample + "17+18/", o.execute)
    #         cmd = "hadd -f"
    #         for year in ["17+18", "2017", "2018"]:
    #             cmd += " " + basePath + sample + year + "/" + histFile
    #             cmds.append(cmd)

    # if o.condor:
    #     DAG.addGeneration()
    # execute(cmds, o.execute, condor_dag=DAG)

def convert(file, script):
    basePath = EOSOUTDIR if o.condor else outputBase
    cmds = []
    for year in years:
        if year not in ['2016']:
            for cps in couplings:
                for cp in cps[0:2]:
                    subdir = cp+year
                    cmd = 'python ZZ4b/nTupleAnalysis/scripts/'+script
                    cmd += ' -i '+basePath+subdir+'/'+file
                    cmds.append( cmd )
            for tt in ['TTTo2L2Nu', 'TTToHadronic', 'TTToSemiLeptonic']:
                subdir = tt+year+'_4b'
                cmd = 'python ZZ4b/nTupleAnalysis/scripts/'+script
                cmd += ' -i '+basePath+subdir+'/'+file
                cmds.append( cmd )
        if year not in ['2016_preVFP', '2016_postVFP']:
            for data in ['_4b', '_3b']:
                subdir = 'data'+year+data
                cmd = 'python ZZ4b/nTupleAnalysis/scripts/'+script
                cmd += ' -i '+basePath+subdir+'/'+file
                cmds.append( cmd )
    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)

def root2h5():
    convert('picoAOD.root', 'convert_root2h5.py')

def h52root():
    convert('picoAOD.h5', 'convert_h52root.py')


def subtractTT():
    basePath = EOSOUTDIR if o.condor else outputBase
    histFile = "hists"+("_j" if o.useJetCombinatoricModel else "")+("_r" if o.reweight else "")+o.histsTag+".root"
    if o.createPicoAOD == "picoAOD.root": histFile = "histsFromNanoAOD.root"
    cmds=[]
    for year in years:
        mkdir(basePath+"qcd"+year, o.execute)
        cmd  = "python ZZ4b/nTupleAnalysis/scripts/subtractTT.py"
        cmd += " -d   "+ basePath+"data"+year+"/"+histFile
        cmd += " --tt "+ basePath+  "TT"+year+"/"+histFile
        cmd += " -q   "+ basePath+ "qcd"+year+"/"+histFile
        cmds.append( cmd )

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)        

    cmds = []
    
    if "2017" in years and "2018" in years and "2016" in years:
        mkdir(basePath + "qcdRunII/", o.execute)
        cmd = "hadd -f"
        for year in ["RunII", "2016", "2017", "2018"]:
            cmd += " " + basePath + "qcd" + year + "/" + histFile
            cmds.append(cmd)
    elif "2017" in years and "2018" in years:
        mkdir(basePath + "qcd17+18/", o.execute)
        cmd = "hadd -f"
        for year in ["17+18", "2017", "2018"]:
            cmd += " " + basePath + "qcd" + year + "/" + histFile
            cmds.append(cmd)
    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)        


def doWeights():
    basePath = EOSOUTDIR if o.condor else outputBase
    if "2016" in years and "2017" in years and "2018" in years:
        weightYears = ["RunII"]
    else:
        weightYears = years
    for year in weightYears:
        mkdir(gitRepoBase+"data"+year, o.execute)
        histFile = "hists"+("_j" if o.useJetCombinatoricModel else "")+("_r" if o.reweight else "")+o.histsTag+".root"
        cmd  = "python ZZ4b/nTupleAnalysis/scripts/makeWeights.py"
        cmd += " -d   "+basePath+"data"+year+"/"+histFile
        cmd += " --tt "+basePath+  "TT"+year+"/"+histFile
        cmd += " -c "+JCMCut
        cmd += " -o "+gitRepoBase+"data"+year+"/ " 
        cmd += " -r "+JCMRegion
        cmd += " -w "+JCMVersion
        cmd += " -y "+year
        cmd += " -l "+lumiDict[year]
        execute(cmd, o.execute)

def doPlots(extraPlotArgs=""):
    plotYears = copy(years)
    if "2016" in years and "2017" in years and "2018" in years:
        plotYears += ["RunII"]
    elif "2017" in years and "2018" in years:
        plotYears += ["17+18"]

    for samples in couplings:
        samples = samples[0:3] + ['data', 'TT']
        if not o.reweight: samples += ['qcd']

        if o.condor: # download hists because repeated EOS access makes plotting about 25% slower
            for year in plotYears:
                for sample in samples:
                    hists = 'hists.root'
                    if sample in ['data', 'TT', 'qcd']:
                        hists = "hists"+("_j" if o.useJetCombinatoricModel else "")+("_r" if o.reweight else "")+".root"
                    cmd = "xrdcp -f "+EOSOUTDIR+sample+year+"/"+hists +" "+ outputBase+sample+year+"/"+hists
                    execute(cmd, o.execute)

    basePath = EOSOUTDIR if o.condor else outputBase    
    plots = "plots"+("_j" if o.useJetCombinatoricModel else "")+("_r" if o.reweight else "")
    if os.path.isdir(outputBase + plots):
        shutil.rmtree(outputBase + plots)
        os.mkdir(outputBase + plots)
    cmds=[]
    for year in plotYears:
        lumi = lumiDict[year]
        cmd  = "python ZZ4b/nTupleAnalysis/scripts/vhh_makePlots.py"
        #cmd += " -i "+basePath # you can uncomment this if you want to make plots directly from EOS
        cmd += " -o "+outputBase
        cmd += " -p "+plots+" -l "+lumi+" -y "+year
        cmd += " -j" if o.useJetCombinatoricModel else ""
        cmd += " -r" if o.reweight else ""
        cmd += " --doJECSyst" if o.doJECSyst else ""
        cmd += " --coupling " + o.coupling
        cmd += " "+extraPlotArgs+" "
        cmds.append(cmd)

    babySit(cmds, o.execute, maxJobs=4)
    cmd = "tar -C "+outputBase+" -zcf "+outputBase+plots+".tar "+plots
    execute(cmd, o.execute)

#
# ML Stuff
#

## in my_env with ROOT and Pandas
# time python ZZ4b/nTupleAnalysis/scripts/convert_root2h5.py -i /uscms/home/bryantp/nobackup/ZZ4b/data2018A/picoAOD.root -o /uscms/home/bryantp/nobackup/ZZ4b/data2018A/picoAOD.h5

## in mlenv4 on cmslpcgpu1
# time python ZZ4b/nTupleAnalysis/scripts/nTagClassifier.py -i /uscms/home/bryantp/nobackup/ZZ4b/data2018A/picoAOD.h5 -l1e-3 -p 0.4 -e 50
## take best model
# time python ZZ4b/nTupleAnalysis/scripts/nTagClassifier.py -i /uscms/home/bryantp/nobackup/ZZ4b/data2018A/picoAOD.h5 -m [best model] -u

## in my_env with ROOT and Pandas
# time python ZZ4b/nTupleAnalysis/scripts/convert_h52root.py -i /uscms/home/bryantp/nobackup/ZZ4b/data2018A/picoAOD.h5 -o /uscms/home/bryantp/nobackup/ZZ4b/data2018A/picoAOD.root


def read_parameter_file(inFileName):
    inFile = open(inFileName,"r")
    outputDict = {}

    for line in inFile:
        words =  line.split()
        if len(words) > 2: 
            words[1]=''.join(words[1:])
            words = words[:2]
        outputDict[words[0]] = words[1]
    return outputDict

def makeCombineHist():
    channelName     = {'lbdt': 'kl', 'sbdt': 'kVV'}
    basis = {'lbdt': -1, 'sbdt': -1}
    histName = 'multijet_background'
    for channel in channelName.keys():
        for region in ['SR', 'CR', 'SB'] + ['Mix'+str(mix) for mix in range(10)]:
            for year in years:
                closureSysts = read_parameter_file('closureFits/nominal_fourier_12bins_VHHTo4B_CV_1_0_C2V_1_0_C3_20_0_RunII/closureResults_VHH_ps_%s_basis%d.txt'%(channel, basis[channel]))
                for systName, variation in closureSysts.iteritems():
                    rootFile = '/uscms/home/'+USER+'/nobackup/VHH/shapefile_VhadHH_'+region+'_'+year+'_'+channelName[channel]+'.root'
                    systName = systName.replace('_VHH_ps_lbdt', '').replace('_VHH_ps_sbdt', '').replace('multijet', '_CMS_bbbb_Multijet')
                    #Multijet closure systematic templates to data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/vhh_makeCombineHists.py -i ' + rootFile
                    cmd +=' -n '+histName+' -a "'+variation + '" --syst ' + systName
                    execute(cmd, o.execute)


#
# Run analysis
#
if o.condor:
    makeTARBALL()

if o.h52root:
    h52root()

if o.makeJECSyst:
    makeJECSyst()

if (o.doSignal or o.doData or o.doTT) and o.condor:
    startEventLoopGeneration = copy( DAG.iG )
    
if o.doSignal:
    doSignal()

if o.doData or o.doTT:
    if o.condor:
        DAG.setGeneration( startEventLoopGeneration )
    doDataTT()

if o.doWeights:
    doWeights()

if o.root2h5:
    root2h5()

if o.xrdcph5:
    xrdcph5(o.xrdcph5)

if o.doQCD:
    subtractTT()

if o.condor:
    DAG.submit(o.execute)

if o.doAccxEff:
    doAccxEff()
    doPlots("-a")

if o.doPlots:
    doPlots("-m")

if o.makeCombineHist:
    makeCombineHist()

