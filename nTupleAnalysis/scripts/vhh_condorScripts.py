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
parser.add_option('-d', '--data', action="store_true", dest = 'data', default =  False, help = 'operate on data root files')
parser.add_option('-s', '--signal', action="store_true", dest = 'signal', default =  False, help = 'operate on signal root files')
parser.add_option('-t', '--ttbar', action="store_true", dest = 'ttbar', default =  False, help = 'operate on ttbar root files')
parser.add_option('--mv', action="store_true", dest = 'move', default =  False, help = 'move files')
parser.add_option('--rm', action="store_true", dest = 'remove', default =  False, help = 'remove files')
parser.add_option('--lpc', action="store_true", dest = 'lpc', default =  False, help = 'operate on lpc')
parser.add_option('--eos', action="store_true", dest = 'eos', default =  False, help = 'operate on eos')
parser.add_option('--hadd', action="store_true", dest = 'hadd', default =  False, help = 'hadd hists')
parser.add_option('-y', '--year', dest = 'years', default =  '2017,2018', help = 'set years')
parser.add_option('--tag', dest = 'tag', default ='', help = 'set tag of picoAOD and hists')
parser.add_option('--oldTag', dest = 'oldTag', default ='', help = 'set old tag of picoAOD')
parser.add_option('--newTag', dest = 'newTag', default ='', help = 'set new tag of picoAOD')
parser.add_option('-j', action="store_true", dest = 'jcm', default = False, help = 'use JCM')
parser.add_option('-r', action="store_true", dest = 'reweight', default = False, help = 'use reweight')
parser.add_option('--debug', action="store_true", dest = 'debug', default = False, help = 'enable debug mode')
parser.add_option('--picoAOD', action="store_true", dest = 'picoAOD', default = False, help = 'operate on picoAOD')
parser.add_option('--hists', action="store_true", dest = 'hists', default = False, help = 'operate on hists')
parser.add_option('--hdf5', action="store_true", dest = 'hdf5', default = False, help = 'operate on hdf5')
parser.add_option('--cp', action="store_true", dest = 'cp', default = False, help = 'copy files')
parser.add_option('--init', action="store_true", dest = 'init', default = False, help = 'initialize dirs and files')
parser.add_option('--coupling', dest = 'coupling', default = ',CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0,C3:20_0', help = 'coupling for signal')
parser.add_option('--classifiers', dest = 'classifiers', default = '', help = 'classifier outputs')
parser.add_option('--nTags', dest = 'nTags', default = '_3b,_4b', help = 'nTag events for ttbar')
parser.add_option('--group', dest = 'group', default = '', help = 'group text files by content')

o, a = parser.parse_args()
classifierFiles = o.classifiers.split(',')

file_tags = o.tag.split(',')

def classifierFile(isSignal = False):
    if not isSignal:
        return classifierFiles
    else:
        return filter(lambda x:x!='FvT',classifierFiles)

def histFile(isSignal = False, tags = file_tags):
  return ['/hists' + ('_j' if not isSignal and o.jcm else '') + ('_r' if not isSignal and o.reweight else '') + tag + '.root' for tag in tags]

def picoAOD(isSignal = False, tags = file_tags):
    return ['/picoAOD'+tag+'.root' for tag in tags]

def classifier(isSignal = False):
    return ['/' + variable + '.root' for variable in classifierFile(isSignal)]

def hdf5(isSignal = False):
    return ['/picoAOD'+tag+'.h5' for tag in file_tags]

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
def eosmkdir(dir):
    run('eos root://cmseos.fnal.gov mkdir ' + eos(dir))
def eosrm(dir):
    run('eos root://cmseos.fnal.gov rm -rf ' + eos(dir))
def xrdcp(src,dest):
    run('xrdcp -f '+('root://cmseos.fnal.gov/' if 'condor' in src else '') + src + ' '+('root://cmseos.fnal.gov/' if 'condor' in dest else '') + dest)    

def lpcmkdir(dir):
    run('mkdir ' + lpc(dir))
def lpccp(src, dest):
    run('cp ' + src + ' ' + dest)
    

def hadd(srcs,dest):
    if len(srcs) > 0:
        print('hadd '+dest)
        cmd = 'hadd -v 0 -f ' + lpc(dest)
        for src in srcs:
            cmd += ' ' + lpc(src)
        run(cmd)

def load_skims():
    oldAOD = picoAOD()
    newAOD = picoAOD(tag='')
    for year in years:
        for cps in signals:
            for cp in cps[0:2]:
                eoscp('VHHSkims/'+cp+year+oldAOD,'VHH/'+cp+year+newAOD)
        # for tt in tts:
        #     eoscp('skims/'+tt+year+oldAOD,'VHH/'+tt+year+newAOD)
        # for data in datas:
        #     eoscp('skims/data'+year+data+oldAOD,'VHH/data'+year+data+newAOD)

def move_eos():
    if o.oldTag == '' and o.newTag == '':
        return
    oldAOD = picoAOD(tag=o.oldTag)[0]
    newAOD = picoAOD(tag=o.newTag)[0]
    for year in years:
        if year not in ['2016']:
            for cps in signals:
                for cp in cps[0:2]:
                    eosmv('VHH/'+cp+year+oldAOD,'VHH/'+cp+year+newAOD)
            for tt in tts:
                for nTag in nTags:
                    eosmv('VHH/'+tt+year+nTag+oldAOD,'VHH/'+tt+year+nTag+newAOD)
        if year not in ['2016_preVFP', '2016_postVFP']:
            for data in datas:
                eosmv('VHH/data'+year+data+oldAOD,'VHH/data'+year+data+newAOD)

def remove_eos():
    if not o.eos: 
        return

    rm_files = []
    if o.hists: rm_files += [histFile]
    if o.picoAOD: rm_files += [picoAOD]
    if o.hdf5: rm_files += [hdf5]
    if o.classifiers: rm_files += [classifier]

    if not rm_files: return

    base = 'VHH/'
    for year in years:
        for cp_file in rm_files:
            if year not in ['2016']:
                for cps in signals:
                    for cp in cps[0:2]:
                        for filename in cp_file(True):
                            file = base + cp+year+filename
                            print(file)
                            eosrm(file)
                for tt in tts:
                    for nTag in nTags:
                        for filename in cp_file():
                            file = base + tt + year + nTag + filename
                            print(file)
                            eosrm(file)
            if year not in ['2016_preVFP', '2016_postVFP']:
                for data in datas:
                    for filename in cp_file():
                        file = base + 'data' + year + data + filename
                        print(file)
                        eosrm(file)

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
    if o.hdf5: cp_files += [hdf5]
    if o.classifiers: cp_files += [classifier]

    if not cp_files: return

    base = 'VHH/'
    for year in years:
        for cp_file in cp_files:
            if year not in ['2016']:
                for cps in signals:
                    for cp in cps[0:2]:
                        for filename in cp_file(True):
                            file = base + cp+year+filename
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
                for boson in cps:
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
                lpcmkdir('VHH/'+cps[2]+'RunII')
                hadd(['VHH/'+cps[2]+year+filename for year in haddYears], 'VHH/'+cps[2]+'RunII'+filename)
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
                    for tag in ['picoAOD'+nTag+'_wJCM', 'FvT_Nominal']:
                        file = '/'+tag+'.root'
                        newFile = file
                        if 'picoAOD' in file:
                            newFile = '/picoAOD.root'
                            filelist = open(full_path('CMSSW_11_1_0_pre5/src/closureTests/ULTrig/fileLists/'+tt+year+nTag+'.txt', lpc, USER),'w')
                            filelist.write('root://cmseos.fnal.gov/'+full_path('VHH/'+tt+year+nTag+ newFile, eos, USER))
                            filelist.close()
                        xrdcp(full_path('ZH4b/ULTrig/'+tt+year+nTag+'_wTrigW'+file, eos, 'jda102'),full_path('VHH/'+tt+year+nTag+newFile, eos, USER))
        if year not in ['2016_preVFP', '2016_postVFP']:
            for n_tag in datas:
                lpcmkdir('VHH/data'+year+n_tag)
                eosmkdir('VHH/data'+year+n_tag)
                for tag in ['picoAOD'+n_tag+'_wJCM', 'FvT_Nominal']:
                    file = '/'+tag+'.root'
                    newFile = file
                    if 'picoAOD' in file:
                        newFile = '/picoAOD.root'
                        filelist = open(full_path('CMSSW_11_1_0_pre5/src/closureTests/ULTrig/fileLists/data'+year+n_tag+'.txt', lpc, USER),'w')
                        filelist.write('root://cmseos.fnal.gov/'+full_path('VHH/data'+year+n_tag + newFile, eos, USER))
                        filelist.close()
                    xrdcp(full_path('ZH4b/ULTrig/data'+year+n_tag+file, eos, 'jda102'),full_path('VHH/data'+year+n_tag+newFile, eos, USER))
    

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

if o.move and o.eos:
    move_eos()
if o.remove and o.eos:
    remove_eos()
if o.hadd and o.lpc:
    hadd_lpc()
if o.cp:
    cp()
if o.init:
    initialize()

if o.group:
    group_files(o.group)

# http://lcginfo.cern.ch/release_packages/x86_64-centos7-gcc8-opt/dev3cuda/ for onnx
# http://lcginfo.cern.ch/release_packages/x86_64-centos7-gcc8-opt/100cuda/
# unset PYTHONPATH
# source /cvmfs/sft.cern.ch/lcg/views/LCG_100cuda/x86_64-centos7-gcc8-opt/setup.sh 

# training
# python ZZ4b/nTupleAnalysis/scripts/vhh_multiClassifier.py -c SvB_MA -s "/uscms/home/chuyuanl/nobackup/VHH/*HHTo4B_CV_*_*_C2V_*_*_C3_*_*_201*/picoAOD.root" -d "/uscms/home/chuyuanl/nobackup/VHH/data201*_3b/picoAOD.root" -t "/uscms/home/chuyuanl/nobackup/VHH/TTTo*201*/picoAOD.root" --train

# to ONNX
# python ZZ4b/nTupleAnalysis/scripts/vhh_multiClassifier.py -c SvB_MA -s "/uscms/home/chuyuanl/nobackup/VHH/*HHTo4B_CV_1_0_C2V_1_0_C3_20_0_201[7-8]/picoAOD.root" -d "/uscms/home/chuyuanl/nobackup/VHH/data201[7-8]_3b/picoAOD.root" -t "/uscms/home/chuyuanl/nobackup/VHH/TTTo*201[7-8]*/picoAOD.root" --train -e 1
# python ZZ4b/nTupleAnalysis/scripts/vhh_multiClassifier.py -c SvB_MA -s "" -d "" -t "" -m "/uscms/home/chuyuanl/nobackup/CMSSW_11_1_0_pre5/src/ZZ4b/nTupleAnalysis/pytorchModels/SvB_MA_HCR+attention_8_np1052_lr0.01_epochs1_offset0_epoch01.pkl" --onnx

# save prediction
# python ZZ4b/nTupleAnalysis/scripts/vhh_multiClassifier.py -c SvB_MA -s "/uscms/home/chuyuanl/nobackup/VHH/*HHTo4B_*_201*/picoAOD.h5" -d "/uscms/home/chuyuanl/nobackup/VHH/data201*/picoAOD.h5" -t "/uscms/home/chuyuanl/nobackup/VHH/TTTo*201*/picoAOD.h5"  --base /uscms/home/chuyuanl/nobackup/CMSSW_11_1_0_pre5/src/ZZ4b/nTupleAnalysis/pytorchModels/ --strategy signalAll,regionC3 -u -m "SvB_MA_HCR+attention_14_np2714_lr0.01_epochs20_offset0_epoch20.pkl"
