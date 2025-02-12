from __future__ import print_function
import time
from copy import copy
import textwrap
import os, re
import sys
import subprocess
import shlex
from glob import glob
import optparse
from threading import Thread
sys.path.insert(0, 'nTupleAnalysis/python/') #https://github.com/patrickbryant/nTupleAnalysis
from commandLineHelpers import *
# sys.path.insert(0, 'PlotTools/python/') #https://github.com/patrickbryant/PlotTools 
# from PlotTools import read_parameter_file
class nameTitle:
    def __init__(self, name, title):
        self.name  = name
        self.title = title

CMSSW = getCMSSW()
USER = getUSER()

EOSOUTDIR = 'root://cmseos.fnal.gov//store/user/'+USER+'/condor/'
CONDOROUTPUTBASE = '/store/user/'+USER+'/condor/'
TARBALL   = 'root://cmseos.fnal.gov//store/user/'+USER+'/condor/'+CMSSW+'.tgz'

parser = optparse.OptionParser()
parser.add_option('--makeFileList',action='store_true',                        default=False, help='Make file list with DAS queries')
parser.add_option('--makeFileListLeptons',action='store_true',                        default=False, help='Make file list with DAS queries')
parser.add_option('-e',            action='store_true', dest='execute',        default=False, help='Execute commands. Default is to just print them')
parser.add_option('-s',            action='store_true', dest='doSignal',       default=False, help='Run signal MC')
parser.add_option('-t',            action='store_true', dest='doTT',           default=False, help='Run ttbar MC')
parser.add_option('-a',            action='store_true', dest='doAccxEff',      default=False, help='Make Acceptance X Efficiency plots')
parser.add_option('-d',            action='store_true', dest='doData',         default=False, help='Run data')
parser.add_option('-q',            action='store_true', dest='doQCD',          default=False, help='Subtract ttbar MC from data to make QCD template')
parser.add_option('-y',                                 dest='year',           default='2016,2017,2018', help='Year or comma separated list of years')
parser.add_option('-o',                                 dest='outputBase',     default='/uscms/home/'+USER+'/nobackup/ZZ4b/', help='path to output')
parser.add_option('-w',            action='store_true', dest='doWeights',      default=False, help='Fit jetCombinatoricModel and nJetClassifier TSpline')
# parser.add_option('--makeJECSyst', action='store_true', dest='makeJECSyst',    default=False, help='Make jet energy correction systematics friend TTrees')
# parser.add_option('--doJECSyst',   action='store_true', dest='doJECSyst',      default=False, help='Run event loop for jet energy correction systematics')
parser.add_option('-j',            action='store_true', dest='useJetCombinatoricModel',       default=False, help='Use the jet combinatoric model')
parser.add_option('-r',            action='store_true', dest='reweight',       default=False, help='Do reweighting with nJetClassifier TSpline')
parser.add_option('--friends',                          dest='friends',        default='', help='Extra friend files. comma separated list where each item replaces picoAOD in the input file, ie FvT,SvB for FvT.root stored in same location as picoAOD.root')
parser.add_option('--bTagSyst',    action='store_true', dest='bTagSyst',       default=False, help='run btagging systematics')
parser.add_option('--plot',        action='store_true', dest='doPlots',        default=False, help='Make Plots')
parser.add_option('-p', '--createPicoAOD',              dest='createPicoAOD',  type='string', help='Create picoAOD with given name')
parser.add_option(      '--subsample',                  dest='subsample',      default=False, action='store_true', help='Make picoAODs which are subsamples of threeTag to emulate fourTag')
parser.add_option(      '--root2h5',                    dest='root2h5',        default=False, action='store_true', help='convert picoAOD.h5 to .root')
parser.add_option(      '--xrdcp',                      dest='xrdcp',          default='', help='copy .h5 or .root files to EOS or NFS')
parser.add_option(      '--h52root',                    dest='h52root',        default=False, action='store_true', help='convert picoAOD.root to .h5')
parser.add_option('-f', '--fastSkim',                   dest='fastSkim',       action='store_true', default=False, help='Do fast picoAOD skim')
parser.add_option(      '--looseSkim',                  dest='looseSkim',      action='store_true', default=False, help='Relax preselection to make picoAODs for JEC Uncertainties which can vary jet pt by a few percent.')
parser.add_option('-n', '--nevents',                    dest='nevents',        default='-1', help='Number of events to process. Default -1 for no limit.')
parser.add_option(      '--detailLevel',                dest='detailLevel',  default='passPreSel,passTTCR,threeTag,fourTag', help='Histogramming detail level. ')
parser.add_option(      '--doTrigEmulation',                                   action='store_true', default=False, help='Emulate the trigger')
parser.add_option(      '--calcTrigWeights',                                   action='store_true', default=False, help='Run trigger emulation from object level efficiencies')
parser.add_option(      '--plotDetailLevel',            dest='plotDetailLevel',  default='passPreSel,passTTCR,threeTag,fourTag,inclusive,outSB,SB,SR,SBSR', help='Histogramming detail level. ')
parser.add_option('-c', '--doCombine',    action='store_true', dest='doCombine',      default=False, help='Make CombineTool input hists')
parser.add_option(   '--loadHemisphereLibrary',    action='store_true', default=False, help='load Hemisphere library')
parser.add_option(   '--noDiJetMassCutInPicoAOD',    action='store_true', default=False, help='create Output Hemisphere library')
parser.add_option(   '--createHemisphereLibrary',    action='store_true', default=False, help='create Output Hemisphere library')
parser.add_option(   '--maxNHemis',    default=10000, help='Max nHemis to load')
parser.add_option(   '--inputHLib3Tag', default='$PWD/data18/hemiSphereLib_3TagEvents_*root',          help='Base path for storing output histograms and picoAOD')
parser.add_option(   '--inputHLib4Tag', default='$PWD/data18/hemiSphereLib_4TagEvents_*root',           help='Base path for storing output histograms and picoAOD')
parser.add_option(   '--SvB_ONNX', action='store_true', default=False,           help='Run ONNX version of SvB model. Model path specified in analysis.py script')
parser.add_option(   '--condor',   action='store_true', default=False,           help='Run on condor')
parser.add_option(   '--conda_pack', action='store_true', default=False,           help='make conda pack')
parser.add_option(   '--dag', dest='dag', default='analysis.dag',           help='.dag file name')
o, a = parser.parse_args()

fromNANOAOD = (o.createPicoAOD == 'picoAOD.root' or o.createPicoAOD == 'none') 

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
script   = 'ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py'
years    = o.year.split(',')
lumiDict = {
    # Old lumi
    '2016':  '36.3e3',
    '2016_preVFP': '19.5e3',
    '2016_postVFP': '16.5e3',
    '2017':  '36.7e3',
    '2018':  '59.8e3',
    'RunII':'132.8e3',
    # Updated lumi with name change trigger from 2017 and btag change trigger from 2018
    # '2016':  '36.5e3',
    # '2017':  '41.5e3',
    # '2018':  '60.0e3',
    # '17+18':'101.5e3',
    # 'RunII':'138.0e3',
}
bTagDict = {'2016': '0.6',#'0.3093', #https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation2016Legacy
            '2017': '0.6',#'0.3033', #https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation94X
            '2018': '0.6',#'0.2770'} #https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X
}
outputBase = o.outputBase
#outputBase = os.getcwd()+'/'
gitRepoBase= 'ZZ4b/nTupleAnalysis/weights/'

# File lists
periods = {'2016': 'BCDEFGH',
           '2017': 'BCDEF',
           '2018': 'ABCD'}

# JECSystList = ['_jerUp', '_jerDown',
#                '_jesTotalUp', '_jesTotalDown']

def dataFiles(year):
    #return ['ZZ4b/fileLists/data'+year+period+'.txt' for period in periods[year]]
    files = []
    for period in periods[year]: 
        if fromNANOAOD:
            files += glob('ZZ4b/fileLists/data%s%s_chunk*.txt'%(year,period))
        else:
            files += glob('ZZ4b/fileLists/data%s%s.txt'%(year,period))
    return files

# Jet Combinatoric Model
JCMRegion = 'SB'
JCMVersion = '00-00-02'
JCMCut = 'passPreSel'
def jetCombinatoricModel(year):
    #return gitRepoBase+'data'+year+'/jetCombinatoricModel_'+JCMRegion+'_'+JCMVersion+'.txt'
    return gitRepoBase+'dataRunII/jetCombinatoricModel_'+JCMRegion+'_'+JCMVersion+'.txt'
#reweight = gitRepoBase+'data'+year+'/reweight_'+JCMRegion+'_'+JCMVersion+'.root'

SvB_ONNX = 'ZZ4b/nTupleAnalysis/pytorchModels/SvB_ResNet_8_8_8_np1391_lr0.01_epochs20_epoch20.onnx'


def mcFiles(year, kind='ttbar'):
    if kind=='ttbar':
        processes = ['TTToHadronic', 'TTToSemiLeptonic', 'TTTo2L2Nu']
    if kind=='signal':
        processes = ['ZZ4b', 'ZH4b', 'ggZH4b', 'HH4b']
    files = []
    for process in processes:
        if fromNANOAOD and kind!='signal':
            files += glob('ZZ4b/fileLists/%s%s*_chunk*.txt'%(process, year))
        else:
            #if year == '2016': year = '2016_*VFP'
            if year=='2016' and process!='HH4b': 
                thisyear = '2016_*VFP'
            else: 
                thisyear = year
            files += glob('ZZ4b/fileLists/%s%s.txt'%(process, thisyear))
    return files

def accxEffFiles(year):
    files = [outputBase+'ZZ4b'+year+'/histsFromNanoAOD.root',
             #outputBase+'ZH4b'+year+'/histsFromNanoAOD.root',
             #outputBase+'ggZH4b'+year+'/histsFromNanoAOD.root',
             outputBase+'bothZH4b'+year+'/histsFromNanoAOD.root',
             outputBase+'ZZZHHH4b'+year+'/histsFromNanoAOD.root',
             outputBase+'HH4b'+year+'/histsFromNanoAOD.root',
             ]
    return files

DAG = None
if o.condor:
    DAG = dag(fileName=o.dag)


def getFileListFile(dataset):
    fileList='ZZ4b/fileLists/'
    if '/BTagCSV/' in dataset or '/JetHT/' in dataset: # this is data
        idx = dataset.find('Run201')
        fileList = fileList+'data'+dataset[idx+3:idx+8]+'.txt'
    elif '/TTTo' in dataset: # this is a ttbar MC sample
        idx = dataset.find('_')
        fileList = fileList+dataset[1:idx]
        idx = dataset.find('20UL')
        fileList = fileList+'20'+dataset[idx+4:idx+6]+'.txt'
    elif '/ZZTo4B' in dataset:
        idx = dataset.find('20UL')
        fileList = fileList+'ZZ4b20'+dataset[idx+4:idx+6]+'.txt'
    elif '/ggZH' in dataset:
        idx = dataset.find('20UL')
        fileList = fileList+'ggZH4b20'+dataset[idx+4:idx+6]+'.txt'
    elif '/ZH' in dataset:
        idx = dataset.find('20UL')
        fileList = fileList+'ZH4b20'+dataset[idx+4:idx+6]+'.txt'
    elif 'HHTo4B' in dataset:
        idx = dataset.find('NanoAOD')
        fileList = fileList+'HH4b20'+dataset[idx-2:idx]+'.txt'
    elif '/MuonEG/' in dataset:
        idx = dataset.find('Run201')
        fileList = fileList+'MuonEgData'+dataset[idx+3:idx+8]+'.txt'
    elif '/SingleMuon/' in dataset:
        idx = dataset.find('Run201')
        fileList = fileList+'SingleMuonData'+dataset[idx+3:idx+8]+'.txt'


    if '/NANOAODSIM' in dataset and '20UL16' in dataset:
        if 'preVFP' in dataset: # 2016 MC split by pre/post VFP what ever that means. Has different lumi
            fileList = fileList.replace('.txt','_preVFP.txt')
        else:
            fileList = fileList.replace('.txt', '_postVFP.txt')
    return fileList

def makeFileList():
    #
    # Ultra Legacy (https://gitlab.cern.ch/cms-nanoAOD/nanoaod-doc/-/wikis/Releases/NanoAODv8) (https://twiki.cern.ch/twiki/bin/view/CMS/PdmVSummaryRun2DataProcessing)
    #

    # Data
    # dasgoclient -query="dataset=/BTagCSV/*UL*NanoAODv2*/NANOAOD" 
    # dasgoclient -query="dataset=/JetHT/*UL2018*NanoAODv2*/NANOAOD" 
    # ttbar
    # dasgoclient -query="dataset=/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/*20UL*NanoAOD*v2*/NANOAODSIM"
    # !!!!!! There is no 2017 SemiLeptonic sample with RunIISummer20UL !!!!!!
    # dasgoclient -query="dataset=/TTTo*_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAOD*/NANOAODSIM"
    datasets = [# '/BTagCSV/Run2016B-ver1_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/BTagCSV/Run2016B-ver2_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/BTagCSV/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/BTagCSV/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/BTagCSV/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/BTagCSV/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/BTagCSV/Run2016F-UL2016_MiniAODv1_NanoAODv2-v2/NANOAOD',
                # '/BTagCSV/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/BTagCSV/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',

                '/BTagCSV/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD', # HLT items were not running
                # '/BTagCSV/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/BTagCSV/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/BTagCSV/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD',
                # '/BTagCSV/Run2017F-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',

                # '/JetHT/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/JetHT/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/JetHT/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
                # '/JetHT/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',


                # '/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM',
                # '/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM',
                # '/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM',
                # '/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM',

                # '/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM',
                # '/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM', 
                # '/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM',
                # '/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM',

                # '/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM',
                # '/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM',
                # '/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM',
                # '/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM',

                
                # '/ZZTo4B01j_5f_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM',
                # '/ZZTo4B01j_5f_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v2/NANOAODSIM',
                # '/ZZTo4B01j_5f_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM',
                # '/ZZTo4B01j_5f_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2/NANOAODSIM',

                # '/ZH_HToBB_ZToBB_M-125_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM',
                # '/ZH_HToBB_ZToBB_M-125_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v2/NANOAODSIM',
                # '/ZH_HToBB_ZToBB_M-125_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v2/NANOAODSIM',
                # '/ZH_HToBB_ZToBB_M-125_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2/NANOAODSIM',

                # '/ggZH_HToBB_ZToBB_M-125_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v1/NANOAODSIM',
                # '/ggZH_HToBB_ZToBB_M-125_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v2/NANOAODSIM',
                # '/ggZH_HToBB_ZToBB_M-125_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM',
                # '/ggZH_HToBB_ZToBB_M-125_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM',

                # '/GluGluToHHTo4B_node_SM_13TeV-madgraph/RunIISummer16NanoAODv7-PUMoriond17_Nano02Apr2020_102X_mcRun2_asymptotic_v8-v1/NANOAODSIM',
                # '/GluGluToHHTo4B_node_SM_13TeV-madgraph_correctedcfg/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM',
                # '/GluGluToHHTo4B_node_SM_TuneCP5_PSWeights_13TeV-madgraph-pythia8/RunIIAutumn18NanoAODv7-Nano02Apr2020_102X_upgrade2018_realistic_v21-v1/NANOAODSIM',
            ]
    

    removed = []
    fileLists = []
    for dataset in datasets:
        fileList = getFileListFile(dataset)
        if fileList not in removed:
            cmd = 'rm %s'%fileList
            execute(cmd, o.execute)
            removed.append(fileList)
        cmd = 'dasgoclient -query="file dataset=%s | grep file.name" | sort >> %s'%(dataset, fileList)
        execute(cmd, o.execute)
        if fileList not in fileLists:
            fileLists.append(fileList)

    for fileList in fileLists:
        cmd = "sed -i 's/\/store/root:\/\/cmsxrootd-site.fnal.gov\/\/store/g' %s"%fileList
        # cmd = "sed -i 's/\/store/root:\/\/cmsxrootd.fnal.gov\/\/store/g' %s"%fileList
        # cmd = "sed -i 's/\/store/root:\/\/cms-xrd-global.cern.ch\/\/store/g' %s"%fileList
        execute(cmd, o.execute)
        print('made', fileList)

    for fileList in fileLists:
        if 'TTTo' not in fileList or 'Run201' not in fileList: continue
        print(fileList)
        with open(fileList,'r') as f:
            files = [line for line in f.readlines()]
        nFiles = len(files)
        chunkSize = 10 if 'TT' in fileList else 20
        chunks = [files[i:i+chunkSize] for i in range(0, nFiles, chunkSize)]
        for c, chunk in enumerate(chunks):
            chunkName = fileList.replace('.txt','_chunk%02d.txt'%(c+1))
            with open(chunkName,'w') as f:
                f.writelines(chunk)
            print('made', chunkName)


def makeFileListLeptons():
    #
    # Ultra Legacy (https://gitlab.cern.ch/cms-nanoAOD/nanoaod-doc/-/wikis/Releases/NanoAODv8) (https://twiki.cern.ch/twiki/bin/view/CMS/PdmVSummaryRun2DataProcessing)
    #
    datasets = []
    datasets += [
        '/MuonEG/Run2016B-ver1_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2016B-ver2_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2016F-UL2016_MiniAODv1_NanoAODv2-v2/NANOAOD',
        '/MuonEG/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',

        '/MuonEG/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2017E-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2017F-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',

        '/MuonEG/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/MuonEG/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
    ]


    datasets += [
        '/SingleMuon/Run2016B-ver1_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2016B-ver2_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2016F-HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD',
        '/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD',

        '/SingleMuon/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2017E-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD',
        '/SingleMuon/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD',

        '/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
        '/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD',
    ]
        

    removed = []
    fileLists = []
    for dataset in datasets:
        fileList = getFileListFile(dataset)
        if fileList not in removed:
            cmd = 'rm %s'%fileList
            execute(cmd, o.execute)
            removed.append(fileList)
        cmd = 'dasgoclient -query="file dataset=%s | grep file.name" | sort >> %s'%(dataset, fileList)
        execute(cmd, o.execute)
        if fileList not in fileLists:
            fileLists.append(fileList)

    for fileList in fileLists:
        cmd = "sed -i 's/\/store/root:\/\/cmsxrootd-site.fnal.gov\/\/store/g' %s"%fileList
        # cmd = "sed -i 's/\/store/root:\/\/cms-xrd-global.cern.ch\/\/store/g' %s"%fileList
        execute(cmd, o.execute)
        print('made', fileList)

    for fileList in fileLists:
        print(fileList)
        with open(fileList,'r') as f:
            files = [line for line in f.readlines()]
        nFiles = len(files)
        chunkSize = 10 if 'TT' in fileList else 20
        chunks = [files[i:i+chunkSize] for i in range(0, nFiles, chunkSize)]
        for c, chunk in enumerate(chunks):
            chunkName = fileList.replace('.txt','_chunk%02d.txt'%(c+1))
            with open(chunkName,'w') as f:
                f.writelines(chunk)
            print('made', chunkName)



def makeTARBALL():
    base='/uscms/home/'+USER+'/nobackup/'
    if os.path.exists(base+CMSSW+'.tgz'):
        print('# TARBALL already exists, skip making it')
        return
    cmd  = 'tar -C '+base+' -zcvf '+base+CMSSW+'.tgz '+CMSSW
    cmd += ' --exclude="*.pdf" --exclude="*.jdl" --exclude="*.stdout" --exclude="*.stderr" --exclude="*.log"'
    cmd += ' --exclude=".git" --exclude="PlotTools" --exclude="madgraph" --exclude="*.pkl"'# --exclude="*.root"'#some root files needed for nano_postproc.py jetmetCorrector
    cmd += ' --exclude="toy4b"'
    cmd += ' --exclude="CombineHarvester"'
    cmd += ' --exclude="HiggsAnalysis"'
    cmd += ' --exclude="closureFits"'
    cmd += ' --exclude="genproductions"'
    cmd += ' --exclude="higgsCombine*.root"'
    cmd += ' --exclude="tmp" --exclude="combine" --exclude-vcs --exclude-caches-all'
    execute(cmd, o.execute)
    cmd  = 'ls '+base+' -alh'
    execute(cmd, o.execute)
    cmd = 'xrdfs root://cmseos.fnal.gov/ mkdir /store/user/'+USER+'/condor'
    execute(cmd, o.execute)
    cmd = 'xrdcp -f '+base+CMSSW+'.tgz '+TARBALL
    execute(cmd, o.execute)
    

def conda_pack():
    #conda_env = '/uscms_data/d3/bryantp/mambaforge/envs/coffea-env/lib/python3.8/site-packages/'
    # import coffea
    # conda_env = '/'.join(coffea.__file__.split('/')[:-2])
    # print('# Move supporting python files to conda site:',conda_env)

    # cmd = 'cp ZZ4b/nTupleAnalysis/scripts/MultiClassifierSchema.py '+conda_env
    # execute(cmd, o.execute)
    # cmd = 'cp ZZ4b/nTupleAnalysis/scripts/coffea_analysis.py       '+conda_env
    # execute(cmd, o.execute)
    # cmd = 'cp ZZ4b/nTupleAnalysis/scripts/networks.py              '+conda_env
    # execute(cmd, o.execute)

    cmd = 'conda-pack -f --name coffea-env --output coffea-env.tar.gz --compress-level 6 --exclude "*pandas/*" -j 4'
    execute(cmd, o.execute)


# def makeJECSyst():
#     basePath = EOSOUTDIR if o.condor else outputBase
#     cmds=[]
#     for year in years:
#         for process in ['ZZ4b', 'ZH4b', 'ggZH4b']:
#             cmd  = 'python PhysicsTools/NanoAODTools/scripts/nano_postproc.py '
#             cmd += basePath+process+year+'/ '
#             cmd += basePath+process+year+'/picoAOD.root '
#             cmd += '--friend '
#             cmd += '-I nTupleAnalysis.baseClasses.jetmetCorrectors jetmetCorrector'+year # modules are defined in https://github.com/patrickbryant/nTupleAnalysis/blob/master/baseClasses/python/jetmetCorrectors.py
#             cmds.append(cmd)

#     execute(cmds, o.execute, condor_dag=DAG)


def doSignal():
    basePath = EOSOUTDIR if o.condor else outputBase
    cp = 'xrdcp -f ' if o.condor else 'cp '
    # mv = 'xrdfs root://cmseos.fnal.gov/ mv ' if o.condor else 'mv '

    mkdir(basePath, o.execute)

    cmds=[]
    # JECSysts = ['']
    # if o.doJECSyst: 
    #     JECSysts = JECSystList

    # for JECSyst in JECSysts:
    histFile = 'hists.root' #+('_j' if o.useJetCombinatoricModel else '')+('_r' if o.reweight else '')+'.root'
    if fromNANOAOD: histFile = 'histsFromNanoAOD.root'

    for year in years:
        for fileList in mcFiles(year, 'signal'):
            sample = fileList.split('/')[-1].replace('.txt','')
            cmd  = 'nTupleAnalysis '+script
            cmd += ' -i '+fileList
            cmd += ' -o '+basePath
            cmd += ' -y '+year
            if 'preVFP' in fileList:
                cmd += '_preVFP'
                lumi = lumiDict['2016_preVFP']
            elif 'postVFP' in fileList:
                cmd += '_postVFP'
                lumi = lumiDict['2016_postVFP']
            else:
                lumi = lumiDict[year]
            cmd += ' -l '+lumi
            cmd += ' --histDetailLevel '+o.detailLevel
            cmd += ' --histFile '+histFile
            cmd += ' -j '+jetCombinatoricModel(year) if o.useJetCombinatoricModel else ''
            cmd += ' -r ' if o.reweight else ''
            cmd += ' --friends %s'%o.friends if o.friends else ''
            cmd += ' -p '+o.createPicoAOD if o.createPicoAOD else ''
            cmd += ' -f ' if o.fastSkim else ''
            cmd += ' --isMC'
            cmd += ' --bTag '+bTagDict[year]
            cmd += ' --bTagSF'
            cmd += ' --bTagSyst' if o.bTagSyst else ''
            cmd += ' --doTrigEmulation' #if o.doTrigEmulation else ''
            cmd += ' --calcTrigWeights' if o.calcTrigWeights else ''
            cmd += ' --passZeroTrigWeight'
            cmd += ' --nevents '+o.nevents
            #cmd += ' --looseSkim' if o.looseSkim else ''
            cmd += ' --looseSkim' if (o.createPicoAOD or o.looseSkim) else '' # For signal samples we always want the picoAOD to be loose skim
            cmd += ' --SvB_ONNX '+SvB_ONNX if o.SvB_ONNX else ''
            # cmd += ' --JECSyst '+JECSyst if JECSyst else ''
            if o.createPicoAOD and o.createPicoAOD != 'none':
                if o.createPicoAOD != 'picoAOD.root':
                    cmd += '; '+cp+basePath+sample+'/'+o.createPicoAOD+' '+basePath+sample+'/picoAOD.root'

            cmds.append(cmd)

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)

    cmds = []
    if '2016' in years: # need to combine pre/postVFP hists
        # for JECSyst in JECSysts:
        histFile = 'hists.root' #+('_j' if o.useJetCombinatoricModel else '')+('_r' if o.reweight else '')+'.root'
        if fromNANOAOD: histFile = 'histsFromNanoAOD.root'
        for sg in ['ZZ4b', 'ZH4b', 'ggZH4b']:
            mkdir(basePath+sg+'2016', o.execute)
            cmd = 'hadd -f '+basePath+sg+'2016/'+histFile+' '+basePath+sg+'2016_preVFP/'+histFile+' '+basePath+sg+'2016_postVFP/'+histFile
            cmd += '' if o.condor else ' > hadd.log'
            cmds.append(cmd)
        if o.condor:
            DAG.addGeneration()
        execute(cmds, o.execute, condor_dag=DAG)

    # Add different signals together within years
    cmds = []
    for year in years:

        # for JECSyst in JECSysts:
        histFile = 'hists.root' #+('_j' if o.useJetCombinatoricModel else '')+('_r' if o.reweight else '')+'.root'
        if fromNANOAOD: histFile = 'histsFromNanoAOD.root'

        # files = mcFiles(year, 'signal')
        # if 'ZZ4b/fileLists/ZH4b'+year+'.txt' in files and 'ZZ4b/fileLists/ggZH4b'+year+'.txt' in files:
        mkdir(basePath+'bothZH4b'+year, o.execute)
        cmd = 'hadd -f '+basePath+'bothZH4b'+year+'/'+histFile+' '+basePath+'ZH4b'+year+'/'+histFile+' '+basePath+'ggZH4b'+year+'/'+histFile
        cmd += '' if o.condor else ' > hadd.log'
        cmds.append(cmd)

        # if 'ZZ4b/fileLists/ZH4b'+year+'.txt' in files and 'ZZ4b/fileLists/ggZH4b'+year+'.txt' in files and 'ZZ4b/fileLists/ZZ4b'+year+'.txt' in files:
        mkdir(basePath+'ZZZHHH4b'+year, o.execute)
        cmd = 'hadd -f '+basePath+'ZZZHHH4b'+year+'/'+histFile+' '+basePath+'ZH4b'+year+'/'+histFile+' '+basePath+'ggZH4b'+year+'/'+histFile+' '+basePath+'ZZ4b'+year+'/'+histFile+' '+basePath+'HH4b'+year+'/'+histFile
        cmd += '' if o.condor else ' > hadd.log'
        cmds.append(cmd)

    if o.condor: 
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)

    # Add years
    cmds = []
    if '2016' in years and '2017' in years and '2018' in years:
        # for JECSyst in JECSysts:
        histFile = 'hists.root' #+('_j' if o.useJetCombinatoricModel else '')+('_r' if o.reweight else '')+'.root'

        if fromNANOAOD: histFile = 'histsFromNanoAOD.root'

        for sample in ['ZZ4b', 'ZH4b', 'ggZH4b', 'bothZH4b', 'ZZZHHH4b', 'HH4b']:
            cmd  = 'hadd -f '+basePath+sample+'RunII/'+histFile+' '
            cmd += basePath+sample+'2016/'+histFile+' '
            cmd += basePath+sample+'2017/'+histFile+' '
            cmd += basePath+sample+'2018/'+histFile+' '
            cmd += '' if o.condor else ' > hadd.log'
            cmds.append(cmd)
                
    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)

      
def doAccxEff():   
    plotYears = copy(years)
    if '2016' in years and '2017' in years and '2018' in years:
        plotYears += ['RunII']
    # if '2016' in plotYears:
    #     plotYears = ['2016_preVFP', '2016_postVFP']+plotYears
    #     #plotYears = ['2016_postVFP']+plotYears

    if o.condor: # download hists because repeated EOS access makes plotting about 25% slower
        samples = ['ZZ4b', 'bothZH4b', 'ZZZHHH4b', 'HH4b']
        for year in plotYears:
            for sample in samples:
                hists = 'histsFromNanoAOD.root'
                cmd = 'xrdcp -f '+EOSOUTDIR+sample+year+'/'+hists +' '+ outputBase+sample+year+'/'+hists
                execute(cmd, o.execute)

    cmds = []

    for year in plotYears:
        for signal in accxEffFiles(year):
            cmd = 'python ZZ4b/nTupleAnalysis/scripts/makeAccxEff.py -i '+signal
            cmds.append(cmd)
    #babySit(cmds, o.execute)
    execute(cmds, o.execute)

def doDataTT():
    basePath = EOSOUTDIR if o.condor else outputBase
    cp = 'xrdcp -f ' if o.condor else 'cp '

    mkdir(basePath, o.execute)

    # run event loop
    cmds=[]
    histFile = 'hists'+('_j' if o.useJetCombinatoricModel else '')+('_r' if o.reweight else '')+'.root'
    if fromNANOAOD: histFile = 'histsFromNanoAOD.root'

    for year in years:
        files = []
        if o.doData: files += dataFiles(year)
        if o.doTT:   files += mcFiles(year)
        nFiles = len(files)
        if o.subsample: files = files*10
        for i, fileList in enumerate(files):
            cmd  = 'nTupleAnalysis '+script
            cmd += ' -i '+fileList
            cmd += ' -o '+basePath
            cmd += ' -y '+year
            if 'preVFP' in fileList:
                cmd += '_preVFP'
            if 'postVFP' in fileList:
                cmd += '_postVFP'
            cmd += ' --histDetailLevel '+o.detailLevel
            if o.subsample:
                vX = i//nFiles
                cmd += ' --histFile '+histFile.replace('.root','_subsample_v%d.root'%(vX))
            else:
                cmd += ' --histFile '+histFile
            cmd += ' -j '+jetCombinatoricModel(year) if o.useJetCombinatoricModel else ''
            cmd += ' -r ' if o.reweight else ''
            cmd += ' --friends %s'%o.friends if o.friends else ''
            if o.subsample:
                cmd += ' -p picoAOD_subsample_v%d.root '%(vX)
                cmd += ' --emulate4bFrom3b --emulationOffset %d '%(vX)
            else:
                cmd += ' -p '+o.createPicoAOD if o.createPicoAOD else ''
            cmd += ' -f ' if o.fastSkim else ''
            cmd += ' --bTag '+bTagDict[year]
            cmd += ' --nevents '+o.nevents
            if fileList in mcFiles(year):
                # if '2016' in fileList:
                if 'preVFP' in fileList:
                    lumi = lumiDict['2016_preVFP']
                elif 'postVFP' in fileList: 
                    lumi = lumiDict['2016_postVFP']
                else:
                    lumi = lumiDict[year]
                cmd += ' -l '+lumi
                cmd += ' --bTagSF'
                #cmd += ' --bTagSyst' if o.bTagSyst else ''
                cmd += ' --doTrigEmulation' #if o.doTrigEmulation else ''
                cmd += ' --calcTrigWeights' if o.calcTrigWeights else ''
                cmd += ' --isMC '
            if o.createHemisphereLibrary  and fileList not in ttbarFiles:
                cmd += ' --createHemisphereLibrary '
            if o.noDiJetMassCutInPicoAOD:
                cmd += ' --noDiJetMassCutInPicoAOD '
            if o.loadHemisphereLibrary:
                cmd += ' --loadHemisphereLibrary '
                cmd += ' --inputHLib3Tag '+o.inputHLib3Tag
                cmd += ' --inputHLib4Tag '+o.inputHLib4Tag
            cmd += ' --SvB_ONNX '+SvB_ONNX if o.SvB_ONNX else ''

            if o.createPicoAOD and o.createPicoAOD != 'none' and not o.subsample:
                if o.createPicoAOD != 'picoAOD.root':
                    sample = fileList.split('/')[-1].replace('.txt','')
                    cmd += '; '+cp+basePath+sample+'/'+o.createPicoAOD+' '+basePath+sample+'/picoAOD.root'

            cmds.append(cmd)

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)

    if o.subsample:
        return

    # combine chunked picoAODs if we just skimmed them from the NANOAODs
    cmds = []
    if o.createPicoAOD == 'picoAOD.root':
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
                processes = ['TTToHadronic'+year, 'TTToSemiLeptonic'+year, 'TTTo2L2Nu'+year]
                if year == '2016': 
                    processes = [p+'_preVFP' for p in processes] + [p+'_postVFP' for p in processes]
                for process in processes:
                    cmd  = 'hadd -f %s%s/picoAOD.root'%(basePath, process)
                    nChunks = len(glob('ZZ4b/fileLists/%s_chunk*.txt'%(process)))
                    for chunk in range(1,nChunks+1):
                        cmd += ' %s%s_chunk%02d/picoAOD.root'%(basePath, process, chunk)
                    cmds.append(cmd)

                    cmd  = 'hadd -f %s%s/histsFromNanoAOD.root'%(basePath, process)
                    for chunk in range(1,nChunks+1):
                        cmd += ' %s%s_chunk%02d/histsFromNanoAOD.root'%(basePath, process, chunk)
                    cmds.append(cmd)

        if o.condor:
            DAG.addGeneration()
        execute(cmds, o.execute, condor_dag=DAG)
        return
                    

    cmds = []
    if o.doTT and '2016' in years: # need to combine pre/postVFP hists
        for tt in ['TTToHadronic', 'TTToSemiLeptonic', 'TTTo2L2Nu']:
            mkdir(basePath+tt+'2016', o.execute)
            cmd = 'hadd -f '+basePath+tt+'2016/'+histFile+' '+basePath+tt+'2016_preVFP/'+histFile+' '+basePath+tt+'2016_postVFP/'+histFile
            cmd += '' if o.condor else ' > hadd.log'
            cmds.append(cmd)
        if o.condor:
            DAG.addGeneration()
        execute(cmds, o.execute, condor_dag=DAG)
        

    # make combined histograms for plotting purposes
    cmds = []
    for year in years:
        if o.doData:
            mkdir(basePath+'data'+year, o.execute)
            cmd = 'hadd -f '+basePath+'data'+year+'/'+histFile+' '+' '.join([basePath+'data'+year+period+'/'+histFile for period in periods[year]])
            cmd += '' if o.condor else ' > hadd.log'
            cmds.append(cmd)
    
        if o.doTT:
            # files = mcFiles(year)
            # if 'ZZ4b/fileLists/TTToHadronic'+year+'.txt' in files and 'ZZ4b/fileLists/TTToSemiLeptonic'+year+'.txt' in files and 'ZZ4b/fileLists/TTTo2L2Nu'+year+'.txt' in files:
            mkdir(basePath+'TT'+year, o.execute)
            cmd = 'hadd -f '+basePath+'TT'+year+'/'+histFile+' '+basePath+'TTToHadronic'+year+'/'+histFile+' '+basePath+'TTToSemiLeptonic'+year+'/'+histFile+' '+basePath+'TTTo2L2Nu'+year+'/'+histFile
            cmd += '' if o.condor else ' > hadd.log'
            cmds.append(cmd)

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)

    cmds = []
    if '2016' in years and '2017' in years and '2018' in years:
        for sample in ['data', 'TT']:
            cmd  = 'hadd -f '+basePath+sample+'RunII/'+histFile+' '
            cmd += basePath+sample+'2016/'+histFile+' '
            cmd += basePath+sample+'2017/'+histFile+' '
            cmd += basePath+sample+'2018/'+histFile+' '
            cmd += '' if o.condor else ' > hadd.log'
            cmds.append(cmd)
                
    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)


def root2h5():
    basePath = EOSOUTDIR if o.condor else outputBase
    cmds = []
    for year in years:
        if not o.subsample:
            for process in ['ZZ4b', 'ggZH4b', 'ZH4b', 'HH4b']:
                subdir = process+year
                cmd = 'python ZZ4b/nTupleAnalysis/scripts/convert_root2h5.py'
                cmd += ' -i '+basePath+subdir+'/picoAOD.root'
                cmds.append( cmd )

        picoAODs = ['picoAOD']
        if o.subsample:
            picoAODs = ['picoAOD_subsample_v%d'%vX for vX in range(10)]
        
        for picoAOD in picoAODs:
            for period in periods[year]:
                subdir = 'data'+year+period
                cmd = 'python ZZ4b/nTupleAnalysis/scripts/convert_root2h5.py'
                cmd += ' -i '+basePath+subdir+'/%s.root'%picoAOD
                cmds.append( cmd )                

            processes = ['TTToHadronic'+year, 'TTToSemiLeptonic'+year, 'TTTo2L2Nu'+year]
            if year == '2016': 
                processes = [p+'_preVFP' for p in processes] + [p+'_postVFP' for p in processes]
            for process in processes:
                cmd = 'python ZZ4b/nTupleAnalysis/scripts/convert_root2h5.py'
                cmd += ' -i '+basePath+process+'/%s.root'%picoAOD
                cmds.append( cmd )

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)


def xrdcp(destination_file): # "NFS picoAOD.root" or "EOS FvT.root,SvB.root,SvB_MA.root"
    destination = destination_file.split()[0]
    names       = destination_file.split()[1].split(',')
    cmds = []
    TO   = EOSOUTDIR  if 'EOS' in destination else outputBase
    FROM = outputBase if 'EOS' in destination else EOSOUTDIR
    for year in years:
        processes = ['ZZ4b'+year, 'ggZH4b'+year, 'ZH4b'+year, 'HH4b'+year]
        if year == '2016':
            processes = ['ZZ4b2016_preVFP', 'ZZ4b2016_postVFP', 'ggZH4b2016_preVFP', 'ggZH4b2016_postVFP', 'ZH4b2016_preVFP', 'ZH4b2016_postVFP', 'HH4b2016']
        for process in processes:
            for name in names:
                cmd = 'xrdcp -f %s%s/%s %s%s/%s'%(FROM,process,name, TO,process,name)
                cmds.append( cmd )

        if o.subsample:
            names = ['picoAOD_subsample_v%d%s'%(vX, extension) for vX in range(10)]

        for name in names:
            for period in periods[year]:
                cmd = 'xrdcp -f %sdata%s%s/%s %sdata%s%s/%s'%(FROM, year, period, name, TO, year, period, name)
                cmds.append( cmd )                

            processes = ['TTToHadronic'+year, 'TTToSemiLeptonic'+year, 'TTTo2L2Nu'+year]
            if year == '2016': 
                processes = [p+'_preVFP' for p in processes] + [p+'_postVFP' for p in processes]
            for process in processes:
                cmd = 'xrdcp -f %s%s/%s %s%s/%s'%(FROM, process, name, TO, process, name)
                cmds.append( cmd )

    for cmd in cmds: execute(cmd, o.execute)    


def h52root():
    basePath = EOSOUTDIR if o.condor else outputBase
    cmds = []
    for year in years:
        for process in ['ZZ4b', 'ggZH4b', 'ZH4b', 'HH4b']:
            subdir = process+year
            cmd = 'python ZZ4b/nTupleAnalysis/scripts/convert_h52root.py'
            cmd += ' -i '+basePath+subdir+'/picoAOD.h5'
            cmds.append( cmd )

        for period in periods[year]:
            subdir = 'data'+year+period
            cmd = 'python ZZ4b/nTupleAnalysis/scripts/convert_h52root.py'
            cmd += ' -i '+basePath+subdir+'/picoAOD.h5'
            cmds.append( cmd )                

        processes = ['TTToHadronic'+year, 'TTToSemiLeptonic'+year, 'TTTo2L2Nu'+year]
        if year == '2016': 
            processes = [p+'_preVFP' for p in processes] + [p+'_postVFP' for p in processes]
        for process in processes:
            cmd = 'python ZZ4b/nTupleAnalysis/scripts/convert_h52root.py'
            cmd += ' -i '+basePath+process+'/picoAOD.h5'
            cmds.append( cmd )

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)
    


def subtractTT():
    basePath = EOSOUTDIR if o.condor else outputBase
    histFile = 'hists'+('_j' if o.useJetCombinatoricModel else '')+('_r' if o.reweight else '')+'.root'
    if o.createPicoAOD == 'picoAOD.root': histFile = 'histsFromNanoAOD.root'
    cmds=[]
    for year in years:
        mkdir(basePath+'qcd'+year, o.execute)
        cmd  = 'python ZZ4b/nTupleAnalysis/scripts/subtractTT.py'
        cmd += ' -d   '+ basePath+'data'+year+'/'+histFile
        cmd += ' --tt '+ basePath+  'TT'+year+'/'+histFile
        cmd += ' -q   '+ basePath+ 'qcd'+year+'/'+histFile
        cmds.append( cmd )

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)        

    cmds = []
    if '2016' in years and '2017' in years and '2018' in years:
        mkdir(basePath+'qcdRunII', o.execute)
        cmd  = 'hadd -f '+basePath+'qcdRunII/'+histFile+' '
        cmd += basePath+'qcd2016/'+histFile+' '
        cmd += basePath+'qcd2017/'+histFile+' '
        cmd += basePath+'qcd2018/'+histFile+' '
        cmd += '' if o.condor else ' > hadd.log'
        cmds.append( cmd )

    if o.condor:
        DAG.addGeneration()
    execute(cmds, o.execute, condor_dag=DAG)        


def doWeights():
    basePath = EOSOUTDIR if o.condor else outputBase
    if '2016' in years and '2017' in years and '2018' in years:
        weightYears = ['RunII']
    else:
        weightYears = years
    for year in weightYears:
        mkdir(gitRepoBase+'data'+year, o.execute)
        histFile = 'hists'+('_j' if o.useJetCombinatoricModel else '')+('_r' if o.reweight else '')+'.root'
        cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeWeights.py'
        cmd += ' -d   '+basePath+'data'+year+'/'+histFile
        cmd += ' --tt '+basePath+  'TT'+year+'/'+histFile
        cmd += ' -c '+JCMCut
        cmd += ' -o '+gitRepoBase+'data'+year+'/ ' 
        cmd += ' -r '+JCMRegion
        cmd += ' -w '+JCMVersion
        cmd += ' -y '+year
        cmd += ' -l '+lumiDict[year]
        execute(cmd, o.execute)


def doPlots(extraPlotArgs=''):
    plotYears = copy(years)
    if '2016' in years and '2017' in years and '2018' in years and 'RunII' not in years:
        plotYears += ['RunII']

    if o.condor and extraPlotArgs != '-a': # download hists because repeated EOS access makes plotting about 25% slower
        samples = ['data', 'TT', 'ZZ4b', 'ZH4b', 'ggZH4b', 'bothZH4b', 'ZZZHHH4b', 'HH4b']
        if not o.reweight: samples += ['qcd']
        for year in plotYears:
            for sample in samples:
                hists = 'hists.root'
                if sample in ['data', 'TT', 'qcd']:
                    hists = 'hists'+('_j' if o.useJetCombinatoricModel else '')+('_r' if o.reweight else '')+'.root'
                cmd = 'xrdcp -f '+EOSOUTDIR+sample+year+'/'+hists +' '+ outputBase+sample+year+'/'+hists
                execute(cmd, o.execute)

    basePath = EOSOUTDIR if o.condor else outputBase    
    plots = 'plots'+('_j' if o.useJetCombinatoricModel else '')+('_r' if o.reweight else '')#+('_combine' if extraPlotArgs=='-c')
    cmds=[]
    for year in plotYears:
        lumi = lumiDict[year]
        cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makePlots.py'
        #cmd += ' -i '+basePath # you can uncomment this if you want to make plots directly from EOS
        cmd += ' -o '+outputBase
        cmd += ' -p '+plots+' -l '+lumi+' -y '+year
        cmd += ' -j' if o.useJetCombinatoricModel else ''
        cmd += ' -r' if o.reweight else ''
        # cmd += ' --doJECSyst' if o.doJECSyst else ''
        cmd += ' --histDetailLevel '+o.plotDetailLevel
        cmd += ' '+extraPlotArgs+' '
        cmds.append(cmd)

    babySit(cmds, o.execute, maxJobs=4)
    cmd = 'tar -C '+outputBase+' -zcf '+outputBase+plots+'.tar '+plots
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

def impactPlots(workspace, expected=True):
    fitType = 'exp' if expected else 'obs'
    cmd  = 'combineTool.py -M Impacts -d ZZ4b/nTupleAnalysis/combine/%s.root --doInitialFit '%workspace
    cmd += '--setParameterRanges rZZ=-10,10:rZH=-10,10:rHH=-10,10 '
    cmd += '--setParameters rZZ=1,rZH=1,rHH=1 --robustFit 1 %s -m 125'%('-t -1' if expected else '')
    execute(cmd, o.execute)
    cmd  = 'combineTool.py -M Impacts -d ZZ4b/nTupleAnalysis/combine/%s.root --doFits       '%workspace
    cmd += '--setParameterRanges rZZ=-10,10:rZH=-10,10:rHH=-10,10 '
    cmd += '--setParameters rZZ=1,rZH=1,rHH=1 --robustFit 1 %s -m 125 --parallel 4'%('-t -1' if expected else '')
    execute(cmd, o.execute)
    cmd = 'combineTool.py -M Impacts -d ZZ4b/nTupleAnalysis/combine/%s.root -o impacts_%s_%s.json -m 125'%(workspace, workspace, fitType)
    execute(cmd, o.execute)
    cmd = 'plotImpacts.py -i impacts_%s_%s.json -o impacts_%s_%s_ZZ --POI rZZ --per-page 20 --left-margin 0.3 --height 400 --label-size 0.04 --translate ZZ4b/nTupleAnalysis/combine/nuisance_names.json'%(workspace, fitType, workspace, fitType)
    execute(cmd, o.execute)
    cmd = 'plotImpacts.py -i impacts_%s_%s.json -o impacts_%s_%s_ZH --POI rZH --per-page 20 --left-margin 0.3 --height 400 --label-size 0.04 --translate ZZ4b/nTupleAnalysis/combine/nuisance_names.json'%(workspace, fitType, workspace, fitType)
    execute(cmd, o.execute)
    cmd = 'plotImpacts.py -i impacts_%s_%s.json -o impacts_%s_%s_HH --POI rHH --per-page 20 --left-margin 0.3 --height 400 --label-size 0.04 --translate ZZ4b/nTupleAnalysis/combine/nuisance_names.json'%(workspace, fitType, workspace, fitType)
    execute(cmd, o.execute)
    execute('rm higgsCombine*.root', o.execute)

def doCombine():

    region='SR'
    cut = 'passPreSel'

    # JECSysts = ['']
    # if o.doJECSyst: 
    #     JECSysts += JECSystList

    mixName = '3bDvTMix4bDvT'
    mixFile = 'ZZ4b/nTupleAnalysis/combine/hists_closure_'+mixName+'_'+region+'_weights_newSBDef.root'
    channels = []
    channels.append('zz')
    channels.append('zh')
    channels.append('hh')
    classifiers = []
    classifiers.append('SvB')
    classifiers.append('SvB_MA')

    doCombineInputs = False
    doWorkspaces    = False
    doPostfitPlots  = False
    doImpacts       = False
    doBreakdown     = False
    doSensitivity   = False
    doProjection    = False

    # doCombineInputs = True
    doWorkspaces    = True
    doPostfitPlots  = True
    doImpacts       = True
    doBreakdown     = True
    doSensitivity   = True
    doProjection    = True

    for classifier in classifiers:
        outFileData = 'ZZ4b/nTupleAnalysis/combine/hists_%s.root'%classifier
        outFileMix  = 'ZZ4b/nTupleAnalysis/combine/hists_closure_%s.root'%classifier
        rebin = {'zz':  4, 'zh':  5, 'hh': 10}
        if 'MA' in classifier:
            mixFile = mixFile.replace('weights_', 'weights_MA_')


        if doCombineInputs:
            execute('rm '+outFileData, o.execute)
            execute('rm '+outFileMix,  o.execute)
            execute('rm '+outFileData.replace('hists_','hists_no_rebin_'), o.execute)
            for year in years:

                for ch in channels:
                    var = classifier+'_ps_'+ch
                    for signal in [nameTitle('ZZ','ZZ4b'), nameTitle('ZH','bothZH4b'), nameTitle('HH', 'HH4b')]:
                        #Sigmal templates to data file
                        cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i /uscms/home/'+USER+'/nobackup/ZZ4b/'+signal.title+year+'/hists.root'
                        cmd += ' -o '+outFileData+' -r '+region+' --var '+var+' --channel '+ch+year+' -n '+signal.name+' --tag four  --cut '+cut+' --rebin '+str(rebin[ch])
                        cmd += ' --systematics /uscms/home/'+USER+'/nobackup/ZZ4b/systematics.pkl'
                        # cmd += ' --systematics_sub_dict '+classifier+'/'+signal.name.lower()+year[-1]
                        execute(cmd, o.execute)

                        #Signal templates to mixed data file
                        cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i /uscms/home/'+USER+'/nobackup/ZZ4b/'+signal.title+year+'/hists.root'
                        cmd += ' -o '+outFileMix +' -r '+region+' --var '+var+' --channel '+ch+year+' -n '+signal.name+' --tag four  --cut '+cut+' --rebin '+str(rebin[ch])
                        cmd += ' --systematics /uscms/home/'+USER+'/nobackup/ZZ4b/systematics.pkl'
                        # cmd += ' --systematics_sub_dict '+classifier+'/'+signal.name.lower()+year[-1]
                        execute(cmd, o.execute)

                        #
                        # No Rebin
                        #
                        #Sigmal templates to data file
                        cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i /uscms/home/'+USER+'/nobackup/ZZ4b/'+signal.title+year+'/hists.root'
                        cmd += ' -o '+outFileData.replace('hists_','hists_no_rebin_')+' -r '+region+' --var '+var+' --channel '+ch+year+' -n '+signal.name+' --tag four  --cut '+cut+' --rebin 2'
                        cmd += ' --systematics /uscms/home/'+USER+'/nobackup/ZZ4b/systematics.pkl'
                        # cmd += ' --systematics_sub_dict '+classifier+'/'+signal.name.lower()+year[-1]
                        execute(cmd, o.execute)


                    closureResultsFile = 'ZZ4b/nTupleAnalysis/combine/closureResults_%s_%s.pkl'%(classifier, ch)

                    #Multijet template to data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i /uscms/home/'+USER+'/nobackup/ZZ4b/data'+year+'/hists_j_r.root'
                    cmd += ' -o '+outFileData+' -r '+region+' --var '+var+' --channel '+ch+year+' -n mj --tag three --cut '+cut+' --rebin '+str(rebin[ch])#+' --errorScale 1.414 '
                    cmd += ' --systematics '+closureResultsFile
                    execute(cmd, o.execute)

                    #Multijet template to mixed data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i '+mixFile
                    cmd += ' -o '+outFileMix +' --TDirectory '+mixName+'_v0/'+ch+year+' --channel '+ch+year+' --var multijet -n mj --rebin '+str(rebin[ch])#+' --errorScale 1.414 '
                    cmd += ' --systematics '+closureResultsFile
                    execute(cmd, o.execute)

                    #ttbar template to data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i /uscms/home/'+USER+'/nobackup/ZZ4b/TT'+year+'/hists_j_r.root'
                    cmd += ' -o '+outFileData+' -r '+region+' --var '+var+' --channel '+ch+year+' -n tt    --tag four  --cut '+cut+' --rebin '+str(rebin[ch])
                    execute(cmd, o.execute)

                    #ttbar template to mixed data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i '+mixFile
                    cmd += ' -o '+outFileMix +' --TDirectory '+mixName+'_v0/'+ch+year+' --channel '+ch+year+' --var ttbar -n tt --rebin '+str(rebin[ch])
                    execute(cmd, o.execute)

                    #data_obs to data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i /uscms/home/'+USER+'/nobackup/ZZ4b/data'+year+'/hists_j_r.root'
                    cmd += ' -o '+outFileData+' -r '+region+' --var '+var+' --channel '+ch+year+' -n data_obs --tag four  --cut '+cut+' --rebin '+str(rebin[ch])
                    execute(cmd, o.execute)

                    #mix data_obs to mixed data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i '+mixFile
                    cmd += ' -o '+outFileMix +' --TDirectory '+mixName+'_v0/'+ch+year+' --channel '+ch+year+' --var data_obs -n data_obs --rebin '+str(rebin[ch])
                    execute(cmd, o.execute)

                    #
                    # No Rebin
                    #
                    #Multijet template to data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i /uscms/home/'+USER+'/nobackup/ZZ4b/data'+year+'/hists_j_r.root'
                    cmd += ' -o '+outFileData.replace('hists_','hists_no_rebin_')+' -r '+region+' --var '+var+' --channel '+ch+year+' -n mj --tag three --cut '+cut+' --rebin 2'
                    # cmd += ' --systematics '+closureResultsFile
                    execute(cmd, o.execute)

                    #ttbar template to data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i /uscms/home/'+USER+'/nobackup/ZZ4b/TT'+year+'/hists_j_r.root'
                    cmd += ' -o '+outFileData.replace('hists_','hists_no_rebin_')+' -r '+region+' --var '+var+' --channel '+ch+year+' -n tt    --tag four  --cut '+cut+' --rebin 2'
                    execute(cmd, o.execute)

                    #data_obs to data file
                    cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeCombineHists.py -i /uscms/home/'+USER+'/nobackup/ZZ4b/data'+year+'/hists_j_r.root'
                    cmd += ' -o '+outFileData.replace('hists_','hists_no_rebin_')+' -r '+region+' --var '+var+' --channel '+ch+year+' -n data_obs --tag four  --cut '+cut+' --rebin 2'
                    execute(cmd, o.execute)


        # doPlots('-c')

        if doWorkspaces:
            # Make data cards
            cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeDataCard.py'
            cmd += ' ZZ4b/nTupleAnalysis/combine/combine_%s.txt'%classifier
            cmd += ' hists_%s.root'%classifier
            cmd += ' ~/nobackup/ZZ4b/systematics.pkl'
            cmd += ' ZZ4b/nTupleAnalysis/combine/closureResults_%s_'%classifier
            execute(cmd, o.execute)

            cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeDataCard.py'
            cmd += ' ZZ4b/nTupleAnalysis/combine/combine_closure_%s.txt'%classifier
            cmd += ' hists_closure_%s.root'%classifier
            cmd += ' ~/nobackup/ZZ4b/systematics.pkl'
            cmd += ' ZZ4b/nTupleAnalysis/combine/closureResults_%s_'%classifier
            execute(cmd, o.execute)

            # Using https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/
            # and https://github.com/cms-analysis/CombineHarvester
            cmd  = "text2workspace.py ZZ4b/nTupleAnalysis/combine/combine_%s.txt "%classifier
            cmd += "-P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose "
            cmd += "--PO 'map=.*/ZZ:rZZ[1,-10,10]' "
            cmd += "--PO 'map=.*/ZH:rZH[1,-10,10]' "
            cmd += "--PO 'map=.*/HH:rHH[1,-10,10]' "
            execute(cmd, o.execute)

            cmd  = "text2workspace.py ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.txt "%classifier
            cmd += "-P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose "
            cmd += "--PO 'map=.*/ZZ:rZZ[1,-10,10]' "
            cmd += "--PO 'map=.*/ZH:rZH[1,-10,10]' "
            cmd += "--PO 'map=.*/HH:rHH[1,-10,10]' "
            execute(cmd, o.execute)

            cmd = "text2workspace.py ZZ4b/nTupleAnalysis/combine/combine_closure_%s.txt "%classifier
            cmd += "-P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose "
            cmd += "--PO 'map=.*/ZZ:rZZ[1,-10,10]' "
            cmd += "--PO 'map=.*/ZH:rZH[1,-10,10]' "
            cmd += "--PO 'map=.*/HH:rHH[1,-10,10]' "
            execute(cmd, o.execute)


        mkpath('combinePlots/'+classifier, o.execute)

        if doPostfitPlots:
            # do background only fit
            cmd = 'combine -M MultiDimFit --setParameters rZZ=0,rZH=0,rHH=0 --freezeParameters rZZ,rZH,rHH --robustFit 1 -n .fit_b --saveWorkspace --saveFitResult -d ZZ4b/nTupleAnalysis/combine/combine_closure_%s.root'%classifier
            execute(cmd, o.execute)
            execute('mv higgsCombine.fit_b.MultiDimFit.mH120.root combinePlots/%s/'%classifier, o.execute)
            execute('mv  multidimfit.fit_b.root                   combinePlots/%s/'%classifier, o.execute)
            # make TH1s of pre/post fit
            cmd = 'PostFitShapesFromWorkspace -w combinePlots/%s/higgsCombine.fit_b.MultiDimFit.mH120.root -f combinePlots/%s/multidimfit.fit_b.root:fit_mdf --total-shapes --postfit --output combinePlots/%s/postfit_closure_b.root'%(classifier,classifier,classifier)
            execute(cmd, o.execute)

            # get best fit signal strengths
            cmd = 'combine -M MultiDimFit --setParameters rZZ=1,rZH=1,rHH=1 --robustFit 1 -n .fit_s --saveWorkspace --saveFitResult -d ZZ4b/nTupleAnalysis/combine/combine_closure_%s.root'%classifier
            execute(cmd, o.execute)
            execute('mv higgsCombine.fit_s.MultiDimFit.mH120.root combinePlots/%s/'%classifier, o.execute)
            execute('mv  multidimfit.fit_s.root                   combinePlots/%s/'%classifier, o.execute)
            # make TH1s of pre/post fit
            cmd = 'PostFitShapesFromWorkspace -w combinePlots/%s/higgsCombine.fit_s.MultiDimFit.mH120.root -f combinePlots/%s/multidimfit.fit_s.root:fit_mdf --total-shapes --postfit --output combinePlots/%s/postfit_closure_s.root'%(classifier,classifier,classifier)
            execute(cmd, o.execute)

            cmd = 'python ZZ4b/nTupleAnalysis/scripts/addPostfitShapes.py combinePlots/%s/postfit_closure_b.root'%(classifier)
            execute(cmd, o.execute)
            cmd = 'python ZZ4b/nTupleAnalysis/scripts/addPostfitShapes.py combinePlots/%s/postfit_closure_s.root'%(classifier)
            execute(cmd, o.execute)
            cmd = 'python ZZ4b/nTupleAnalysis/scripts/makePlots.py     -c combinePlots/%s/postfit_closure'%(classifier)
            execute(cmd, o.execute)


        if doImpacts:
            impactPlots('combine_closure_%s'%classifier, expected=False)
            impactPlots('combine_%s'%classifier,         expected=True)
            cmd = 'mv impacts_combine_* combinePlots/'+classifier+'/'
            execute(cmd, o.execute)


        if doBreakdown:
            for ch in channels:
            #for ch in ['hh']:
                fit = 'combine -M MultiDimFit -t -1 --robustFit 1 --setParameters rZZ=1,rZH=1,rHH=1'
                cmd = '%s --saveWorkspace -d ZZ4b/nTupleAnalysis/combine/combine_%s.root -n .%s_postfit'%(fit, classifier, ch)
                execute(cmd, o.execute)
                fit = 'combine -M MultiDimFit -t -1 --robustFit 1 --setParameters rZZ=1,rZH=1,rHH=1 -P r%s --algo grid --alignEdges 1 --points 41'%ch.upper()
                fit = '%s --snapshotName MultiDimFit -d higgsCombine.%s_postfit.MultiDimFit.mH120.root'%(fit, ch)
                cmd = '%s -n .%s_total'%(fit, ch)
                execute(cmd, o.execute)
                cmd = '%s -n .%s_freeze_multijet --freezeNuisanceGroups multijet'%(fit, ch)
                execute(cmd, o.execute)
                cmd = '%s -n .%s_freeze_btag     --freezeNuisanceGroups multijet,btag'%(fit, ch)
                execute(cmd, o.execute)
                # cmd = '%s -n .%s_freeze_junc     --freezeNuisanceGroups multijet,btag,junc'%(fit, ch)
                # execute(cmd, o.execute)
                # cmd = '%s -n .%s_freeze_all      --freezeNuisanceGroups multijet,btag,junc,others'%(fit, ch)
                # execute(cmd, o.execute)
                cmd = '%s -n .%s_freeze_all      --freezeNuisanceGroups multijet,btag,others'%(fit, ch)
                execute(cmd, o.execute)
                execute('mv higgsCombine.*.MultiDimFit.mH120.root combinePlots/%s/'%classifier, o.execute)

                cmd  = 'plot1DScan.py '
                cmd += 'combinePlots/%s/higgsCombine.%s_total.MultiDimFit.mH120.root --main-label "Total uncert." --others '%(classifier, ch)
                cmd += 'combinePlots/%s/higgsCombine.%s_freeze_multijet.MultiDimFit.mH120.root:"Multijet":2 '%(classifier, ch)
                cmd += 'combinePlots/%s/higgsCombine.%s_freeze_btag.MultiDimFit.mH120.root:"b-tagging":4 '%(classifier, ch)
                # cmd += 'combinePlots/%s/higgsCombine.%s_freeze_junc.MultiDimFit.mH120.root:"Jet Unc.":9 '%(classifier, ch)
                cmd += 'combinePlots/%s/higgsCombine.%s_freeze_all.MultiDimFit.mH120.root:"Stat. only":3 '%(classifier, ch)
                cmd += '--y-max 10 --y-cut 12 --breakdown "multijet,btag,others,stat" --translate ZZ4b/nTupleAnalysis/combine/nuisance_names.json '
                cmd += '--POI r%s -o combinePlots/%s/breakdown_%s'%(ch.upper(), classifier, ch)
                execute(cmd, o.execute)
            execute('rm combinePlots/*/*.png', o.execute)
            execute('rm combinePlots/*/breakdown*.root', o.execute)


        if doSensitivity:
            cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_%s.txt --expectSignal=1 -t -1       > combinePlots/%s/expected_significance.txt'%(classifier,classifier)
            execute(cmd, o.execute)
            cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_%s.txt --expectSignal=0 --run blind > combinePlots/%s/expected_limit.txt'%(classifier,classifier)
            execute(cmd, o.execute)

            cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_%s.root --redefineSignalPOIs rZZ --setParameters rZH=1,rHH=1 -t -1       > combinePlots/%s/expected_significance_zz.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_%s.root --redefineSignalPOIs rZZ --setParameters rZH=0,rHH=0 --run blind > combinePlots/%s/expected_limit_zz.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd  = 'combine -M MultiDimFit --algo cross --cl=0.68 -t -1 --robustFit 1 --setParameters rZZ=1,rZH=1,rHH=1 -P rZZ -d ZZ4b/nTupleAnalysis/combine/combine_%s.root'%classifier
            cmd += '; cp higgsCombineTest.MultiDimFit.mH120.root combinePlots/%s/higgsCombine.expected_rZZ.root'%classifier
            execute(cmd, o.execute)
            cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_%s.root --redefineSignalPOIs rZH --setParameters rZZ=1,rHH=1 -t -1       > combinePlots/%s/expected_significance_zh.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_%s.root --redefineSignalPOIs rZH --setParameters rZZ=0,rHH=0 --run blind > combinePlots/%s/expected_limit_zh.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd  = 'combine -M MultiDimFit --algo cross --cl=0.68 -t -1 --robustFit 1 --setParameters rZZ=1,rZH=1,rHH=1 -P rZH -d ZZ4b/nTupleAnalysis/combine/combine_%s.root'%classifier
            cmd += '; cp higgsCombineTest.MultiDimFit.mH120.root combinePlots/%s/higgsCombine.expected_rZH.root'%classifier
            execute(cmd, o.execute)
            cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_%s.root --redefineSignalPOIs rHH --setParameters rZZ=1,rZH=1 -t -1       > combinePlots/%s/expected_significance_hh.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_%s.root --redefineSignalPOIs rHH --setParameters rZZ=0,rZH=0 --run blind > combinePlots/%s/expected_limit_hh.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd  = 'combine -M MultiDimFit --algo cross --cl=0.68 -t -1 --robustFit 1 --setParameters rZZ=1,rZH=1,rHH=1 -P rHH -d ZZ4b/nTupleAnalysis/combine/combine_%s.root'%classifier
            cmd += '; cp higgsCombineTest.MultiDimFit.mH120.root combinePlots/%s/higgsCombine.expected_rHH.root'%classifier
            execute(cmd, o.execute)

            # Stat only
            cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.txt --expectSignal=1 -t -1       > combinePlots/%s/expected_stat_only_significance.txt'%(classifier,classifier)
            execute(cmd, o.execute)
            cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.txt --expectSignal=0 --run blind > combinePlots/%s/expected_stat_only_limit.txt'%(classifier,classifier)
            execute(cmd, o.execute)

            cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.root --redefineSignalPOIs rZZ --setParameters rZH=1,rHH=1 -t -1       > combinePlots/%s/expected_stat_only_significance_zz.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.root --redefineSignalPOIs rZZ --setParameters rZH=0,rHH=0 --run blind > combinePlots/%s/expected_stat_only_limit_zz.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd  = 'combine -M MultiDimFit --algo cross --cl=0.68 -t -1 --robustFit 1 --setParameters rZZ=1,rZH=1,rHH=1 -P rZZ -d ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.root'%classifier
            cmd += '; cp higgsCombineTest.MultiDimFit.mH120.root combinePlots/%s/higgsCombine.expected_stat_only_rZZ.root'%classifier
            execute(cmd, o.execute)
            cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.root --redefineSignalPOIs rZH --setParameters rZZ=1,rHH=1 -t -1       > combinePlots/%s/expected_stat_only_significance_zh.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.root --redefineSignalPOIs rZH --setParameters rZZ=0,rHH=0 --run blind > combinePlots/%s/expected_stat_only_limit_zh.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd  = 'combine -M MultiDimFit --algo cross --cl=0.68 -t -1 --robustFit 1 --setParameters rZZ=1,rZH=1,rHH=1 -P rZH -d ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.root'%classifier
            cmd += '; cp higgsCombineTest.MultiDimFit.mH120.root combinePlots/%s/higgsCombine.expected_stat_only_rZH.root'%classifier
            execute(cmd, o.execute)
            cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.root --redefineSignalPOIs rHH --setParameters rZZ=1,rZH=1 -t -1       > combinePlots/%s/expected_stat_only_significance_hh.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.root --redefineSignalPOIs rHH --setParameters rZZ=0,rZH=0 --run blind > combinePlots/%s/expected_stat_only_limit_hh.txt'%(classifier, classifier)
            execute(cmd, o.execute)
            cmd  = 'combine -M MultiDimFit --algo cross --cl=0.68 -t -1 --robustFit 1 --setParameters rZZ=1,rZH=1,rHH=1 -P rHH -d ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s.root'%classifier
            cmd += '; cp higgsCombineTest.MultiDimFit.mH120.root combinePlots/%s/higgsCombine.expected_stat_only_rHH.root'%classifier
            execute(cmd, o.execute)

            cmd = 'python ZZ4b/nTupleAnalysis/scripts/sensitivity_tables.py %s'%classifier
            execute(cmd, o.execute)
            execute('rm higgsCombine*.root', o.execute)


        if doProjection:
            mkpath('combinePlots/'+classifier+'/future', o.execute)
            
            for future in ['', '_200', '_300', '_500', '_1000', '_2000', '_3000']:
                if future:
                    # Make scaled input hists
                    cmd = 'rm ZZ4b/nTupleAnalysis/combine/hists_%s%s.root'%(classifier, future.replace('_',''))
                    execute(cmd, o.execute)
                    cmd = 'python ZZ4b/nTupleAnalysis/scripts/makeLumiScaledHists.py ZZ4b/nTupleAnalysis/combine/hists_%s.root %s'%(classifier, future.replace('_',''))
                    execute(cmd, o.execute)
                    cmd = 'rm ZZ4b/nTupleAnalysis/combine/hists_no_rebin_%s%s.root'%(classifier, future)
                    execute(cmd, o.execute)
                    cmd = 'python ZZ4b/nTupleAnalysis/scripts/makeLumiScaledHists.py ZZ4b/nTupleAnalysis/combine/hists_no_rebin_%s.root %s'%(classifier, future.replace('_',''))
                    execute(cmd, o.execute)

                # Make data cards
                cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeDataCard.py'
                cmd += ' ZZ4b/nTupleAnalysis/combine/combine_%s%s.txt'%(classifier, future)
                cmd += ' hists_%s%s.root'%(classifier, future)
                cmd += ' ~/nobackup/ZZ4b/systematics.pkl'
                cmd += ' ZZ4b/nTupleAnalysis/combine/closureResults_%s_'%classifier
                execute(cmd, o.execute)
                cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeDataCard.py'
                cmd += ' ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s%s.txt'%(classifier, future)
                cmd += ' hists_%s%s.root'%(classifier, future)
                execute(cmd, o.execute)
                cmd  = 'python ZZ4b/nTupleAnalysis/scripts/makeDataCard.py'
                cmd += ' ZZ4b/nTupleAnalysis/combine/combine_stat_only_no_rebin_%s%s.txt'%(classifier, future)
                cmd += ' hists_no_rebin_%s%s.root'%(classifier, future)
                cmd += ' ~/nobackup/ZZ4b/systematics.pkl'
                execute(cmd, o.execute)

                # Make workspace
                cmd  = "text2workspace.py ZZ4b/nTupleAnalysis/combine/combine_%s%s.txt "%(classifier, future)
                cmd += "-P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose "
                cmd += "--PO 'map=.*/ZZ:rZZ[1,-10,10]' "
                cmd += "--PO 'map=.*/ZH:rZH[1,-10,10]' "
                cmd += "--PO 'map=.*/HH:rHH[1,-10,10]' "
                execute(cmd, o.execute)
                cmd  = "text2workspace.py ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s%s.txt "%(classifier, future)
                cmd += "-P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose "
                cmd += "--PO 'map=.*/ZZ:rZZ[1,-10,10]' "
                cmd += "--PO 'map=.*/ZH:rZH[1,-10,10]' "
                cmd += "--PO 'map=.*/HH:rHH[1,-10,10]' "
                execute(cmd, o.execute)
                cmd  = "text2workspace.py ZZ4b/nTupleAnalysis/combine/combine_stat_only_no_rebin_%s%s.txt "%(classifier, future)
                cmd += "-P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose "
                cmd += "--PO 'map=.*/ZZ:rZZ[1,-10,10]' "
                cmd += "--PO 'map=.*/ZH:rZH[1,-10,10]' "
                cmd += "--PO 'map=.*/HH:rHH[1,-10,10]' "
                execute(cmd, o.execute)

                # Compute expected significance
                cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_%s%s.root --redefineSignalPOIs rZZ --setParameters rZH=1,rHH=1 -t -1       > combinePlots/%s/future/expected_significance_zz%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_%s%s.root --redefineSignalPOIs rZZ --setParameters rZH=0,rHH=0 --run blind > combinePlots/%s/future/expected_limit_zz%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_%s%s.root --redefineSignalPOIs rZH --setParameters rZZ=1,rHH=1 -t -1       > combinePlots/%s/future/expected_significance_zh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_%s%s.root --redefineSignalPOIs rZH --setParameters rZZ=0,rHH=0 --run blind > combinePlots/%s/future/expected_limit_zh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_%s%s.root --redefineSignalPOIs rHH --setParameters rZZ=1,rZH=1 -t -1       > combinePlots/%s/future/expected_significance_hh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_%s%s.root --redefineSignalPOIs rHH --setParameters rZZ=0,rZH=0 --run blind > combinePlots/%s/future/expected_limit_hh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)

                cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s%s.root --redefineSignalPOIs rZZ --setParameters rZH=1,rHH=1 -t -1       > combinePlots/%s/future/expected_stat_only_significance_zz%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s%s.root --redefineSignalPOIs rZZ --setParameters rZH=0,rHH=0 --run blind > combinePlots/%s/future/expected_stat_only_limit_zz%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s%s.root --redefineSignalPOIs rZH --setParameters rZZ=1,rHH=1 -t -1       > combinePlots/%s/future/expected_stat_only_significance_zh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s%s.root --redefineSignalPOIs rZH --setParameters rZZ=0,rHH=0 --run blind > combinePlots/%s/future/expected_stat_only_limit_zh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s%s.root --redefineSignalPOIs rHH --setParameters rZZ=1,rZH=1 -t -1       > combinePlots/%s/future/expected_stat_only_significance_hh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_%s%s.root --redefineSignalPOIs rHH --setParameters rZZ=0,rZH=0 --run blind > combinePlots/%s/future/expected_stat_only_limit_hh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)

                cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_no_rebin_%s%s.root --redefineSignalPOIs rZZ --setParameters rZH=1,rHH=1 -t -1       > combinePlots/%s/future/expected_stat_only_no_rebin_significance_zz%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_no_rebin_%s%s.root --redefineSignalPOIs rZZ --setParameters rZH=0,rHH=0 --run blind > combinePlots/%s/future/expected_stat_only_no_rebin_limit_zz%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_no_rebin_%s%s.root --redefineSignalPOIs rZH --setParameters rZZ=1,rHH=1 -t -1       > combinePlots/%s/future/expected_stat_only_no_rebin_significance_zh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_no_rebin_%s%s.root --redefineSignalPOIs rZH --setParameters rZZ=0,rHH=0 --run blind > combinePlots/%s/future/expected_stat_only_no_rebin_limit_zh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M Significance     ZZ4b/nTupleAnalysis/combine/combine_stat_only_no_rebin_%s%s.root --redefineSignalPOIs rHH --setParameters rZZ=1,rZH=1 -t -1       > combinePlots/%s/future/expected_stat_only_no_rebin_significance_hh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)
                cmd = 'combine -M AsymptoticLimits ZZ4b/nTupleAnalysis/combine/combine_stat_only_no_rebin_%s%s.root --redefineSignalPOIs rHH --setParameters rZZ=0,rZH=0 --run blind > combinePlots/%s/future/expected_stat_only_no_rebin_limit_hh%s.txt'%(classifier, future, classifier, future)
                execute(cmd, o.execute)

            cmd = 'python ZZ4b/nTupleAnalysis/scripts/makeProjection.py %s'%classifier
            execute(cmd, o.execute)

    # cmd = 'mv higgsCombine* combinePlots/'+classifier+'/'
    # execute(cmd, o.execute)

    # cmd = 'rm -r combinePlots/*/*.root'

    ### Independent fit
    # combine -M MultiDimFit  ZZ4b/nTupleAnalysis/combine/combine.root  -t -1 --setParameterRanges rZZ=-4,6:rZH=-4,6:rHH=-4,6 --setParameters rZZ=1,rZH=1,rHH=1 --algo=grid --points=1000 -n rZZ_rZH_rHH_scan_3d -v 1
    # python plot_scan_2d.py  
    ### Assuming SM
    # cmd = 'combine -M MultiDimFit  ZZ4b/nTupleAnalysis/combine/combine.root  -t -1 --setParameterRanges rZZ=-4,6:rZH=-4,6 --setParameters rZZ=1,rZH=1 --algo singles --cl=0.68'
    # execute(cmd, False)
    # combine -M Significance ZZ4b/nTupleAnalysis/combine/combine.txt   -t -1 --expectSignal=1
    # combine -M Significance ZZ4b/nTupleAnalysis/combine/combineZZ.txt -t -1 --expectSignal=1
    # combine -M Significance ZZ4b/nTupleAnalysis/combine/combineZH.txt -t -1 --expectSignal=1

    # PostFitShapesFromWorkspace -d ZZ4b/nTupleAnalysis/combine/combine_closure.txt -w ZZ4b/nTupleAnalysis/combine/combine_closure.root -f ZZ4b/nTupleAnalysis/combine/combine_closure.root:fit_b --output combine_closure_shapes.root --postfit --sampling --print --total-shapes

#
# Run analysis
#
if o.makeFileList:
    makeFileList()

if o.makeFileListLeptons:
    makeFileListLeptons()

if o.condor:
    makeTARBALL()

if o.conda_pack:
    conda_pack()

if o.h52root:
    h52root()

# if o.makeJECSyst:
#     makeJECSyst()

if (o.doSignal or o.doData or o.doTT) and DAG is not None:
    startEventLoopGeneration = copy( DAG.iG )
if o.doSignal:
    doSignal()

if o.doData or o.doTT:
    if DAG is not None:
        DAG.setGeneration( startEventLoopGeneration )
    doDataTT()

if o.doWeights:
    doWeights()

if o.root2h5:
    root2h5()

if o.xrdcp:
    xrdcp(o.xrdcp)

if o.doQCD:
    subtractTT()

if o.condor:
    DAG.submit(o.execute)
    print('# Use condor_monitor to watch jobs once they have finished submitting')
    # if o.execute and DAG.jobLines:
    #     print '# wait 10s for DAG jobs to start before starting condor_monitor'
    #     time.sleep(10)
    # if DAG.jobLines:
    #     cmd = 'python nTupleAnalysis/python/condor_monitor.py'
    #     execute(cmd, o.execute)

if o.doAccxEff:
    doAccxEff()
    doPlots('-a')

if o.doPlots:
    doPlots('-m')

if o.doCombine:
    doCombine()

