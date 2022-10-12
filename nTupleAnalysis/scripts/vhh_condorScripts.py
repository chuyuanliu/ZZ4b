from functools import partial
import os,sys
import vhh_fileHelper as fh
from copy import copy
from glob import glob
import operator
sys.path.insert(0, 'nTupleAnalysis/python/') #https://github.com/patrickbryant/nTupleAnalysis
from commandLineHelpers import *
import optparse

CMSSW = getCMSSW()
USER = getUSER()
runCount = 0 # TEMP

parser = optparse.OptionParser()
parser.add_option('-d', '--data', action="store_true", dest = 'data', default =  False, help = 'Operate on data root files')
parser.add_option('-s', '--signal', action="store_true", dest = 'signal', default =  False, help = 'Operate on signal root files')
parser.add_option('-t', '--ttbar', action="store_true", dest = 'ttbar', default =  False, help = 'Operate on ttbar root files')
parser.add_option('--mv', action="store_true", dest = 'move', default =  False, help = 'Move files')
parser.add_option('--rm', action="store_true", dest = 'remove', default =  False, help = 'Remove files')
parser.add_option('--lpc', action="store_true", dest = 'lpc', default =  False, help = 'Operate on lpc')
parser.add_option('--eos', action="store_true", dest = 'eos', default =  False, help = 'Operate on eos')
parser.add_option('--hadd', action="store_true", dest = 'hadd', default =  False, help = 'hadd hists')
parser.add_option('-y', '--year', dest = 'years', default =  '2016,2017,2018', help = 'Comma separated list of years')
parser.add_option('--tags', dest = 'tags', default ='', help = 'Set tags for picoAOD and hists')
parser.add_option('--oldTag', dest = 'oldTag', default ='', help = 'Set old tag of picoAOD')
parser.add_option('--newTag', dest = 'newTag', default ='', help = 'Set new tag of picoAOD')
parser.add_option('-j', action="store_true", dest = 'jcm', default = False, help = 'Use JCM')
parser.add_option('-r', action="store_true", dest = 'reweight', default = False, help = 'Use reweight')
parser.add_option('--debug', action="store_true", dest = 'debug', default = False, help = 'Enable debug mode')
parser.add_option('--picoAOD', action="store_true", dest = 'picoAOD', default = False, help = 'Operate on picoAOD')
parser.add_option('--hists', action="store_true", dest = 'hists', default = False, help = 'Operate on hists')
parser.add_option('--cp', action="store_true", dest = 'cp', default = False, help = 'Copy files')
parser.add_option('--init', action="store_true", dest = 'init', default = False, help = 'Initialize dirs and files')
parser.add_option('--coupling', dest = 'coupling', default = ',CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0,C3:20_0', help = 'Couplings of signals')
parser.add_option('--classifiers', dest = 'classifiers', default = '', help = 'Classifier outputs')
parser.add_option('--nTags', dest = 'nTags', default = '_4b', help = 'nTag events for ttbar')
parser.add_option('--group', dest = 'group', default = '', help = 'Group text files by content')

o, a = parser.parse_args()
classifierFiles = list(filter(lambda x: x != '', o.classifiers.split(',')))

file_tags = o.tags.split(',')

def classifierFile(isSignal = False):
    if not isSignal:
        return classifierFiles
    else:
        return filter(lambda x:'FvT' not in x,classifierFiles)

def histFile(isSignal = False, tags = file_tags):
  return ['/hists' + ('_j' if not isSignal and o.jcm else '') + ('_r' if not isSignal and o.reweight else '') + tag + '.root' for tag in tags]

def picoAOD(isSignal = False, tags = file_tags):
    return ['/picoAOD'+tag+'.root' for tag in tags]

def classifier(isSignal = False, tags = file_tags):
    return ['/' + variable + tag + '.root' for variable in classifierFile(isSignal) for tag in tags]

nTags = o.nTags.split(',')
signals = []
if o.signal:
    signals = fh.getCouplingList(o.coupling)

# datas = {'2016': [],
#          '2017': [],
#          '2018': [],
#          '17+18':[]}
datas = []
if o.data:
    datas = ['_4b', '_3b']
    # datas = {'2016': ['B','C','D','E','F','G','H'],
    #          '2017': ['C','D','E','F'],
    #          '2018': ['A','B','C','D'],
    #          '17+18': []}

tts = []
if o.ttbar:
    tts = ['TTTo2L2Nu', 'TTToHadronic', 'TTToSemiLeptonic']

years = o.years.split(',')
if '2016' in years:
    if '2016_preVFP' not in years:
        years += ['2016_preVFP']
    if '2016_postVFP' not in years:
        years += ['2016_postVFP']

def eos(dir, user = USER):
    return '/store/user/' + user + '/condor/' + dir
def lpc(dir, user = USER):
    return '/uscms/home/' + user + '/nobackup/' + dir

def full_path(path, area, user = USER):
    return area(path, user)

def run(cmd):
    global runCount
    runCount += 1
    print(str(runCount).ljust(5) + cmd)
    if not o.debug:
        os.system(cmd)
def eosmv(src, dest):
    run('eos root://cmseos.fnal.gov mv ' + eos(src) + ' ' + eos(dest)) 
def eoscp(src, dest):
    run('eos cp root://cmseos.fnal.gov/' + eos(src) + ' root://cmseos.fnal.gov/' + eos(dest)) 
def eosrm(src):
    run('eos root://cmseos.fnal.gov rm -rf ' + eos(src))
def eosmkdir(src):
    run('eos root://cmseos.fnal.gov mkdir ' + eos(src))

def lpcmv(src, dest):
    run('mv ' + lpc(src) + ' ' + lpc(dest))
def lpccp(src, dest):
    run('cp ' + lpc(src) + ' ' + lpc(dest))
def lpcrm(src):
    run('rm -rf ' + lpc(src))
def lpcmkdir(src):
    if not os.path.isdir(lpc(src)):
        run('mkdir ' + lpc(src))

def xrdcp(src,dest):
    run('xrdcp -f '+('root://cmseos.fnal.gov/' if 'condor' in src else '') + src + ' '+('root://cmseos.fnal.gov/' if 'condor' in dest else '') + dest)    

def hadd(srcs,dest):
    if len(srcs) > 0:
        print('hadd '+dest)
        cmd = 'hadd -v 0 -f ' + lpc(dest)
        for src in srcs:
            cmd += ' ' + lpc(src)
        run(cmd)

def load_skims():
    oldAOD = picoAOD()
    newAOD = picoAOD(tags=[''])
    for year in years:
        for cps in signals:
            for boson in cps[0:2]:
                eoscp('VHHSkims/'+boson+year+oldAOD,'VHH/'+boson+year+newAOD)
        # for tt in tts:
        #     eoscp('skims/'+tt+year+oldAOD,'VHH/'+tt+year+newAOD)
        # for data in datas:
        #     eoscp('skims/data'+year+data+oldAOD,'VHH/data'+year+data+newAOD)

def move():
    mv_years = copy(years)
    mv_tts   = copy(tts)
    cps_max  = 2
    if o.eos: 
        mv = eosmv
    elif o.lpc:
        mv = lpcmv
        mv_years += ['RunII']
        mv_tts   += ['TT']
        cps_max  = 3
    else:
        return   
    if o.oldTag == o.newTag:
        return
    mv_files = []
    if o.hists: mv_files += [histFile]
    if o.picoAOD: mv_files += [picoAOD]
    if o.classifiers: mv_files += [classifier]

    for mv_file in mv_files:
        oldAOD = partial(mv_file, tags=[o.oldTag])
        newAOD = partial(mv_file, tags=[o.newTag])
        for year in mv_years:
            if year not in ['2016']:
                for cps in signals:
                    for boson in cps[0:cps_max]:
                        mv('VHH/'+boson+year+oldAOD(isSignal = True)[0],'VHH/'+boson+year+newAOD(isSignal = True)[0])
                for tt in mv_tts:
                    for nTag in nTags:
                        mv('VHH/'+tt+year+nTag+oldAOD()[0],'VHH/'+tt+year+nTag+newAOD()[0])
            if year not in ['2016_preVFP', '2016_postVFP']:
                for data in datas:
                    mv('VHH/data'+year+data+oldAOD()[0],'VHH/data'+year+data+newAOD()[0])

def remove():
    rm_years = copy(years)
    rm_tts   = copy(tts)
    cps_max  = 2
    if o.eos: 
        rm = eosrm
    elif o.lpc:
        rm = lpcrm
        rm_years += ['RunII']
        rm_tts   += ['TT']
        cps_max  = 3
    else:
        return

    rm_files = []
    if o.hists: rm_files += [histFile]
    if o.picoAOD: rm_files += [picoAOD]
    if o.classifiers: rm_files += [classifier]

    if not rm_files: return

    base = 'VHH/'
    for cp_file in rm_files:
        for year in rm_years:
            if year not in ['2016']:
                for cps in signals:
                    for boson in cps[0:cps_max]:
                        for filename in cp_file(True):
                            file = base + boson + year + filename
                            print(file)
                            rm(file)
                for tt in rm_tts:
                    for nTag in nTags:
                        for filename in cp_file():
                            file = base + tt + year + nTag + filename
                            print(file)
                            rm(file)
            if year not in ['2016_preVFP', '2016_postVFP']:
                for data in datas:
                    for filename in cp_file():
                        file = base + 'data' + year + data + filename
                        print(file)
                        rm(file)

# TODO cp hadded from eos
# TODO hadd use condor

def cp():
    if o.lpc: 
        from_area = lpc
        to_area = eos
    elif o.eos: 
        from_area = eos
        to_area = lpc
    else: return

    cp_files = []
    if o.hists: cp_files += [histFile]
    if o.picoAOD: cp_files += [picoAOD]
    if o.classifiers: cp_files += [classifier]

    if not cp_files: return

    base = 'VHH/'
    for year in years:
        for cp_file in cp_files:
            if year not in ['2016']:
                for cps in signals:
                    for boson in cps[0:2]:
                        for filename in cp_file(True):
                            file = base + boson+year+filename
                            print(file)
                            xrdcp(full_path(file, from_area), full_path(file, to_area))
                for tt in tts:
                    for nTag in nTags:
                        for filename in cp_file():
                            file = base + tt + year + nTag + filename
                            print(file)
                            xrdcp(full_path(file, from_area), full_path(file, to_area))
            if year not in ['2016_preVFP', '2016_postVFP']:
                for data in datas:
                    for filename in cp_file():
                        file = base + 'data' + year + data + filename
                        print(file)
                        xrdcp(full_path(file, from_area), full_path(file, to_area))

def hadd_lpc():
    for year in years:
        if year not in ['2016']:
            for filename in histFile():
                if o.ttbar:
                    for nTag in nTags:
                        lpcmkdir('VHH/TT'+year +nTag)
                        hadd(['VHH/'+tt+year +nTag+filename for tt in tts], 'VHH/TT'+year +nTag+filename)
            for filename in histFile(True):
                for cps in signals:
                    lpcmkdir('VHH/'+cps[2]+year)
                    hadd(['VHH/'+cp+year+filename for cp in cps[0:2]], 'VHH/'+cps[2]+year+filename)
    if '2016' in years:
        haddYears = ['2016_preVFP','2016_postVFP']
        for filename in histFile():
            if o.ttbar:
                for nTag in nTags:
                    lpcmkdir('VHH/TT2016'+nTag)
                    hadd(['VHH/TT'+year +nTag+filename for year in haddYears], 'VHH/TT2016'+nTag+filename)
        for filename in histFile(True):
            for cps in signals:
                for boson in cps[0:3]:
                    lpcmkdir('VHH/'+boson+'2016')
                    hadd(['VHH/'+boson+year+filename for year in haddYears], 'VHH/'+boson+'2016'+filename)
    if '2016' in years and '2017' in years and '2018' in years:
        haddYears = ['2016','2017','2018']
        for filename in histFile():
            for data in datas:
                lpcmkdir('VHH/dataRunII'+data)
                hadd(['VHH/data'+year+data+filename for year in haddYears], 'VHH/dataRunII'+data+filename)
            if o.ttbar:
                for nTag in nTags:
                    lpcmkdir('VHH/TTRunII'+nTag)
                    hadd(['VHH/TT'+year +nTag+filename for year in haddYears], 'VHH/TTRunII'+nTag+filename)
        for filename in histFile(True):
            for cps in signals:
                for boson in cps[0:3]:
                    lpcmkdir('VHH/'+boson+'RunII')
                    hadd(['VHH/'+boson+year+filename for year in haddYears], 'VHH/'+boson+'RunII'+filename)
def initialize():
    # load_skims()
    lpcmkdir('CMSSW_11_1_0_pre5/src/closureTests')
    lpcmkdir('CMSSW_11_1_0_pre5/src/closureTests/UL')
    lpcmkdir('CMSSW_11_1_0_pre5/src/closureTests/UL/fileLists')
    initYears = copy(years)
    for year in initYears:
        if year not in ['2016']:
            for signal in signals:
                for process in signal[0:2]:
                    lpcmkdir('VHH/'+process+year)
                    eosmkdir('VHH/'+process+year)
                    if o.picoAOD:
                        xrdcp(full_path('ZH4b/ULTrig/'+process+year+'/picoAOD_wTrigWeights.root', eos, 'jda102'),full_path('VHH/'+process+year+'/picoAOD.root', eos, USER))
                lpcmkdir('VHH/'+signal[2]+year)
                eosmkdir('VHH/'+signal[2]+year) 
            if o.ttbar:
                for nTag in nTags:
                    lpcmkdir('VHH/TT'+year+nTag)
                    eosmkdir('VHH/TT'+year+nTag)
            for tt in tts:
                for nTag in nTags:
                    lpcmkdir('VHH/'+tt+year+nTag)
                    eosmkdir('VHH/'+tt+year+nTag)
                    for rootFile in [] + (['picoAOD'+nTag+'_wJCM_newSBDef'] if o.picoAOD else []) + (classifierFiles):
                        file = '/'+rootFile+'.root'
                        newFile = file
                        if 'picoAOD' in file:
                            newFile = '/picoAOD.root'
                            filelist = open(full_path('CMSSW_11_1_0_pre5/src/closureTests/ULTrig/fileLists/'+tt+year+nTag+'.txt', lpc, USER),'w')
                            filelist.write('root://cmseos.fnal.gov/'+full_path('VHH/'+tt+year+nTag+ newFile, eos, USER))
                            filelist.close()
                        xrdcp(full_path('ZH4b/ULTrig/'+tt+year+nTag+'_wTrigW'+file, eos, 'jda102'),full_path('VHH/'+tt+year+nTag+newFile, eos, USER))
        if year not in ['2016_preVFP', '2016_postVFP']:
            for nTag in datas:
                lpcmkdir('VHH/data'+year+nTag)
                eosmkdir('VHH/data'+year+nTag)
                for rootFile in [] + (['picoAOD'+nTag+'_wJCM_newSBDef'] if o.picoAOD else []) + (classifierFiles):
                    file = '/'+rootFile+'.root'
                    newFile = file
                    if 'picoAOD' in file:
                        newFile = '/picoAOD.root'
                        filelist = open(full_path('CMSSW_11_1_0_pre5/src/closureTests/ULTrig/fileLists/data'+year+nTag+'.txt', lpc, USER),'w')
                        filelist.write('root://cmseos.fnal.gov/'+full_path('VHH/data'+year+nTag + newFile, eos, USER))
                        filelist.close()
                    xrdcp(full_path('ZH4b/ULTrig/data'+year+nTag+file, eos, 'jda102'),full_path('VHH/data'+year+nTag+newFile, eos, USER))
    

def group_files(path):
    files = glob(path)
    contents = {}
    for file in files:
        with open(file) as f:
            contents[file] = f.read()
    contents = sorted(contents.items(), key = operator.itemgetter(1))
    current = ''
    groups = 0
    for content in contents:
        if current != content[1]:
            current = content[1]
            groups += 1
            print('-' * 20)
            print(groups)
        print(content[0])
    print('total groups ' + str(groups))

if o.move:
    move()
if o.remove:
    remove()
if o.hadd and o.lpc:
    hadd_lpc()
if o.cp:
    cp()
if o.init:
    initialize()

if o.group:
    group_files(o.group)

# cmds
# python ZZ4b/nTupleAnalysis/scripts/vhh_analysis.py -d -t -j -r --separate3b4b -y 2016,2017,2018 --trigger --applyPuIdSF --condor -e --runKlBdt
# python ZZ4b/nTupleAnalysis/scripts/vhh_analysis.py -s -y 2016,2017,2018 --condor --higherOrder --trigger --bTagSyst --puIdSyst --applyPuIdSF -e --friends SvB_MA_VHH_8nc --runKlBdt
# python ZZ4b/nTupleAnalysis/scripts/vhh_condorScripts.py -s -d -t -j -r -y 2016,2017,2018 --cp --eos --hists 
# python ZZ4b/nTupleAnalysis/scripts/vhh_condorScripts.py -s -d -t -j -r -y 2016,2017,2018 --hadd --lpc --hists 
# for JEC
# python ZZ4b/nTupleAnalysis/scripts/vhh_analysis.py -s -y 2016,2017,2018 --condor --higherOrder --trigger --doJECSyst -e --friends SvB_MA_VHH_8nc --runKlBdt
# python ZZ4b/nTupleAnalysis/scripts/vhh_condorScripts.py -s -y 2016,2017,2018 --cp --eos --tag _jesTotalUp,_jesTotalDown,_jerUp,_jerDown --hists
# python ZZ4b/nTupleAnalysis/scripts/vhh_condorScripts.py -s -y 2016,2017,2018 --hadd --lpc --tag _jesTotalUp,_jesTotalDown,_jerUp,_jerDown --hists

# http://lcginfo.cern.ch/release_packages/x86_64-centos7-gcc8-opt/dev3cuda/ for onnx
# http://lcginfo.cern.ch/release_packages/x86_64-centos7-gcc8-opt/100cuda/
# unset PYTHONPATH
# source /cvmfs/sft.cern.ch/lcg/views/LCG_100cuda/x86_64-centos7-gcc8-opt/setup.sh 
# source /cvmfs/sft.cern.ch/lcg/views/dev3cuda/latest/x86_64-centos7-gcc8-opt/setup.sh 

# training
# python ZZ4b/nTupleAnalysis/scripts/vhh_multiClassifier.py -c SvB_MA -s "/uscms/home/chuyuanl/nobackup/VHH/*HHTo4B_CV_*_*_C2V_*_*_C3_*_*_201*/picoAOD.root" -d "/uscms/home/chuyuanl/nobackup/VHH/data201*_3b/picoAOD.root" -t "/uscms/home/chuyuanl/nobackup/VHH/TTTo*201*_4b/picoAOD.root" --train --nFeatures 8 --trainOffset 0,1,2 --normCoupling

# save prediction
# python ZZ4b/nTupleAnalysis/scripts/vhh_multiClassifier.py -c SvB_MA -s "/uscms/home/chuyuanl/nobackup/VHH/*HHTo4B_CV_*_*_C2V_*_*_C3_*_*_201*/picoAOD.root" -d "/uscms/home/chuyuanl/nobackup/VHH/data201*/picoAOD.root" -t "/uscms/home/chuyuanl/nobackup/VHH/TTTo*201*_4b/picoAOD.root" --updatePostFix _VHH --weightFilePostFix _8nc -u -m "ZZ4b/nTupleAnalysis/pytorchModels/SvB_MA_VHH/SvB_MA_HCR+attention_8_np1052_seed0_lr0.01_epochs20_offset*_epoch20.pkl"

# to ONNX
# python ZZ4b/nTupleAnalysis/scripts/vhh_multiClassifier.py -c SvB_MA -s "" -d "" -t "" -m "/uscms/home/chuyuanl/nobackup/CMSSW_11_1_0_pre5/src/ZZ4b/nTupleAnalysis/pytorchModels/SvB_MA_VHH/SvB_MA_HCR+attention_8_np1052_seed0_lr0.01_epochs20_offset*_epoch20.pkl" --onnx

##########experiments##########
## cmds w/o syst, compare classifier
# $TAG=_8,_8n,_8nc,_14,_14nc
# python ZZ4b/nTupleAnalysis/scripts/vhh_multiClassifier.py -c SvB_MA -s "/uscms/home/chuyuanl/nobackup/VHH/*HHTo4B_CV_*_*_C2V_*_*_C3_*_*_201*/picoAOD.root" -d "/uscms/home/chuyuanl/nobackup/VHH/data201*/picoAOD.root" -t "/uscms/home/chuyuanl/nobackup/VHH/TTTo*201*_4b/picoAOD.root" --updatePostFix _VHH --weightFilePostFix $TAG -u -m "ZZ4b/nTupleAnalysis/pytorchModels/SvB_MA_VHH/SvB_MA_HCR+attention_8_np1052_seed0_lr0.01_epochs20_offset*_epoch20.pkl"
# python ZZ4b/nTupleAnalysis/scripts/vhh_analysis.py -d -t -j -r --separate3b4b -y 2016,2017,2018 --trigger --applyPuIdSF --condor -e --friends FvT_Nominal,SvB_MA_VHH$TAG --histsTag $TAG
# python ZZ4b/nTupleAnalysis/scripts/vhh_analysis.py -s -y 2016,2017,2018 --higherOrder --trigger --applyPuIdSF --condor -e --friends SvB_MA_VHH$TAG --histsTag $TAG
# python ZZ4b/nTupleAnalysis/scripts/vhh_condorScripts.py -s -d -t -j -r -y 2016,2017,2018 --cp --eos --hists --tags $TAG
# python ZZ4b/nTupleAnalysis/scripts/vhh_condorScripts.py -s -d -t -j -r -y 2016,2017,2018 --hadd --lpc --hists --tags $TAG