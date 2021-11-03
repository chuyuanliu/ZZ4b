import os,sys
import vhh_fileHelper as fh
from copy import copy
sys.path.insert(0, 'nTupleAnalysis/python/') #https://github.com/patrickbryant/nTupleAnalysis
from commandLineHelpers import *
import optparse

CMSSW = getCMSSW()
USER = getUSER()

parser = optparse.OptionParser()
parser.add_option('-d', '--data', action="store_true", dest = 'data', default =  False, help = 'operate on data root files')
parser.add_option('-s', '--signal', action="store_true", dest = 'signal', default =  False, help = 'operate on signal root files')
parser.add_option('-t', '--ttbar', action="store_true", dest = 'ttbar', default =  False, help = 'operate on ttbar root files')
parser.add_option('--mv', action="store_true", dest = 'move', default =  False, help = 'move skims to input directory')
parser.add_option('--lpc', action="store_true", dest = 'lpc', default =  False, help = 'operate on lpc')
parser.add_option('--eos', action="store_true", dest = 'eos', default =  False, help = 'operate on eos')
parser.add_option('--hadd', action="store_true", dest = 'hadd', default =  False, help = 'hadd hists')
parser.add_option('-y', '--year', dest = 'years', default =  '2017,2018', help = 'set years')
parser.add_option('--tag', dest = 'tag', default ='', help = 'set tag of picoAOD')
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
parser.add_option('--merge', action="store_true", dest = 'merge', default = False, help = 'merge weight into root files')

o, a = parser.parse_args()


def histFile(isSignal = False):
  return '/hists' + ('_j' if not isSignal and o.jcm else '') + ('_r' if not isSignal and o.reweight else '') + '.root'

def picoAOD(isSignal = False):
    return '/picoAOD'+o.tag+'.root'

def hdf5(isSignal = False):
    return '/picoAOD'+o.tag+'.h5'


signals = []
if o.signal:
    signals = fh.getCouplingList(',CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0')

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
    years += ['2016_preVFP', '2016_postVFP']

def eos(dir, user = USER):
    return '/store/user/' + user + '/condor/' + dir
def lpc(dir, user = USER):
    return '/uscms/home/' + user + '/nobackup/' + dir

def full_path(path, area, user = USER):
    return area(path, user)

def run(cmd):
    if o.debug:
        print(cmd)
    else:
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
    oldAOD = '/picoAOD' + o.tag + '.root'
    newAOD = '/picoAOD.root'
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
    oldAOD = '/picoAOD' + o.oldTag + '.root'
    newAOD = '/picoAOD' + o.newTag + '.root'
    for year in years:
        if year not in ['2016', '2016_preVFP', '2016_postVFP']:
            for cps in signals:
                for cp in cps[0:2]:
                    eosmv('VHH/'+cp+year+oldAOD,'VHH/'+cp+year+newAOD)
        if year not in ['2016_preVFP', '2016_postVFP']:
            for data in datas:
                eosmv('VHH/data'+year+data+oldAOD,'VHH/data'+year+data+newAOD)
        if year not in ['2016']:
            for tt in tts:
                eosmv('VHH/'+tt+year+'_4b'+oldAOD,'VHH/'+tt+year+'_4b'+newAOD)

def cp():
    if o.lpc: 
        from_area = lpc
        to_area = eos
    elif o.eos: 
        from_area = eos
        to_area = lpc
    else: return

    if o.hists: cp_files = histFile
    elif o.picoAOD: cp_files = picoAOD
    elif o.hdf5: cp_files = hdf5
    else: return

    base = 'VHH/'
    for year in years:
        if year not in ['2016', '2016_preVFP', '2016_postVFP']:
            for cps in signals:
                for cp in cps[0:2]:
                    file = base + cp+year+cp_files(True)
                    print(file)
                    xrdcp(full_path(file, from_area), full_path(file, to_area))
        if year not in ['2016_preVFP', '2016_postVFP']:
            for data in datas:
                file = base + 'data' + year + data + cp_files()
                print(file)
                xrdcp(full_path(file, from_area), full_path(file, to_area))
        if year not in ['2016']:
            for tt in tts:
                file = base + tt + year + '_4b' + cp_files()
                print(file)
                xrdcp(full_path(file, from_area), full_path(file, to_area))

def hadd_lpc():
    for year in years:
        if year not in ['2016', '2016_preVFP', '2016_postVFP']:
            for cps in signals:
                lpcmkdir('VHH/'+cps[2]+year)
                hadd(['VHH/'+cp+year+histFile(True) for cp in cps[0:2]], 'VHH/'+cps[2]+year+histFile(True))
        if year not in ['2016']:
            lpcmkdir('VHH/TT'+year +'_4b')
            hadd(['VHH/'+tt+year +'_4b'+histFile() for tt in tts], 'VHH/TT'+year +'_4b'+histFile())
    if '2017' in years and '2018' in years:
        haddYears = ['2017','2018']
        for cps in signals:
            for cp in cps[0:3]:
                lpcmkdir('VHH/'+cp+'17+18')
                hadd(['VHH/'+cp+year+histFile(True) for year in haddYears], 'VHH/'+cp+'17+18'+histFile(True))
        if o.ttbar:
            lpcmkdir('VHH/TT17+18_4b')
            hadd(['VHH/TT'+year +'_4b'+histFile() for year in haddYears], 'VHH/TT17+18_4b'+histFile())
        for data in datas:
            lpcmkdir('VHH/data17+18'+data)
            hadd(['VHH/data'+year+data+histFile() for year in haddYears], 'VHH/data17+18'+data+histFile())
    if '2016_preVFP' in years and '2016_postVFP' in years:
        haddYears = ['2016_preVFP', '2016_postVFP']
        if o.ttbar:
            lpcmkdir('VHH/TT2016_4b')
            hadd(['VHH/TT'+year +'_4b'+histFile() for year in haddYears], 'VHH/TT2016_4b'+histFile())
    if '2016' in years and '2017' in years and '2018' in years:
        haddYears = ['2016','2017','2018']
        if o.ttbar:
            lpcmkdir('VHH/TTRunII_4b')
            hadd(['VHH/TT'+year +'_4b'+histFile() for year in haddYears], 'VHH/TTRunII_4b'+histFile())
        for data in datas:
            lpcmkdir('VHH/dataRunII'+data)
            hadd(['VHH/data'+year+data+histFile() for year in haddYears], 'VHH/dataRunII'+data+histFile())

def initialize():
    load_skims()
    lpcmkdir('CMSSW_11_1_0_pre5/src/closureTests')
    lpcmkdir('CMSSW_11_1_0_pre5/src/closureTests/UL')
    lpcmkdir('CMSSW_11_1_0_pre5/src/closureTests/UL/fileLists')
    initYears = copy(years)
    for year in initYears:
        lpcmkdir('VHH/TT'+year+'_4b')
        eosmkdir('VHH/TT'+year+'_4b')
        if year not in ['2016']:
            for tt in tts:
                lpcmkdir('VHH/'+tt+year+'_4b')
                eosmkdir('VHH/'+tt+year+'_4b')
                for tag in ['_4b_wJCM', '_4b_wJCM_SvB_FvT']:
                    file = '/picoAOD'+tag+'.root'
                    xrdcp(full_path('ZH4b/UL/'+tt+year+'_4b'+file, eos, 'jda102'),full_path('VHH/'+tt+year+'_4b'+file, eos, 'chuyuanl'))
                    filelist = open(full_path('CMSSW_11_1_0_pre5/src/closureTests/UL/fileLists/'+tt+year+tag.replace('_wJCM','')+'.txt', lpc, 'chuyuanl'),'w')
                    filelist.write('root://cmseos.fnal.gov/'+full_path('VHH/'+tt+year+'_4b'+('/picoAOD.root' if o.merge else file), eos, 'chuyuanl'))
                    filelist.close()
        if year not in ['2016_preVFP', '2016_postVFP']:
            for n_tag in datas:
                lpcmkdir('VHH/data'+year+n_tag)
                eosmkdir('VHH/data'+year+n_tag)
                for tag in ['_wJCM', '_wJCM_SvB_FvT']:
                    file = '/picoAOD'+n_tag+tag+'.root'
                    xrdcp(full_path('ZH4b/UL/data'+year+n_tag+file, eos, 'jda102'),full_path('VHH/data'+year+n_tag+file, eos, 'chuyuanl'))
                    filelist = open(full_path('CMSSW_11_1_0_pre5/src/closureTests/UL/fileLists/data'+year+n_tag+tag.replace('_wJCM','')+'.txt', lpc, 'chuyuanl'),'w')
                    filelist.write('root://cmseos.fnal.gov/'+full_path('VHH/data'+year+n_tag+('/picoAOD.root' if o.merge else file), eos, 'chuyuanl'))
                    filelist.close()        
    
if o.move and o.eos:
    move_eos()
if o.hadd and o.lpc:
    hadd_lpc()
if o.cp:
    cp()
if o.init:
    initialize()

#root://cmseos.fnal.gov//store/user/bryantp/condor/data201*/picoAOD.root 
#root://cmseos.fnal.gov//store/user/bryantp/condor/TT*201*/picoAOD.root 

# 4b:

# nTupleAnalysis ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py -i closureTests/UL//fileLists/data2016_4b_wJCM.txt  --inputWeightFiles closureTests/UL//fileLists/data2016_4b_wJCM_SvB_FvT.txt -o root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/UL/  -p NONE  -y 2016 --bTag 0.6  --histFile hists_4b_wFvT_Nominal.root --histDetailLevel fourTag.passMDRs.passMjjOth.HHSR.passSvB --jcmNameLoad Nominal -r --FvTName  FvT_Nominal
# nTupleAnalysis ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py -i closureTests/UL//fileLists/data2017_4b_wJCM.txt  --inputWeightFiles closureTests/UL//fileLists/data2017_4b_wJCM_SvB_FvT.txt -o root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/UL/  -p NONE  -y 2017 --bTag 0.6  --histFile hists_4b_wFvT_Nominal.root --histDetailLevel fourTag.passMDRs.passMjjOth.HHSR.passSvB --jcmNameLoad Nominal -r --FvTName  FvT_Nominal
# nTupleAnalysis ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py -i closureTests/UL//fileLists/data2018_4b_wJCM.txt  --inputWeightFiles closureTests/UL//fileLists/data2018_4b_wJCM_SvB_FvT.txt -o root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/UL/  -p NONE  -y 2018 --bTag 0.6  --histFile hists_4b_wFvT_Nominal.root --histDetailLevel fourTag.passMDRs.passMjjOth.HHSR.passSvB --jcmNameLoad Nominal -r --FvTName  FvT_Nominal


# 3b:
# nTupleAnalysis ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py -i closureTests/UL//fileLists/data2016_3b_wJCM.txt  --inputWeightFiles closureTests/UL//fileLists/data2016_3b_wJCM_SvB_FvT.txt -o root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/UL/  -p NONE  -y 2016 --bTag 0.6  --histFile hists_3b_wFvT_Nominal.root --histDetailLevel threeTag.passMDRs.passMjjOth.HHSR.passSvB --jcmNameLoad Nominal -r --FvTName  FvT_Nominal
# nTupleAnalysis ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py -i closureTests/UL//fileLists/data2017_3b_wJCM.txt  --inputWeightFiles closureTests/UL//fileLists/data2017_3b_wJCM_SvB_FvT.txt -o root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/UL/  -p NONE  -y 2017 --bTag 0.6  --histFile hists_3b_wFvT_Nominal.root --histDetailLevel threeTag.passMDRs.passMjjOth.HHSR.passSvB --jcmNameLoad Nominal -r --FvTName  FvT_Nominal
# nTupleAnalysis ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py -i closureTests/UL//fileLists/data2018_3b_wJCM.txt  --inputWeightFiles closureTests/UL//fileLists/data2018_3b_wJCM_SvB_FvT.txt -o root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/UL/  -p NONE  -y 2018 --bTag 0.6  --histFile hists_3b_wFvT_Nominal.root --histDetailLevel threeTag.passMDRs.passMjjOth.HHSR.passSvB --jcmNameLoad Nominal -r --FvTName  FvT_Nominal


# all the text files can be found: on lxplus
# eg:
# > cat /uscms/home/jda102/nobackup/HH4b/CMSSW_11_1_3/src/closureTests/UL//fileLists/data2016_3b_wJCM.txt
# root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/UL//data2016_3b/picoAOD_3b_wJCM.root

# TTbar (only need the 4b sample)
# nTupleAnalysis ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py -i closureTests/UL//fileLists/TTTo2L2Nu2017_4b_wJCM.txt  --inputWeightFiles closureTests/UL//fileLists/TTTo2L2Nu2017_4b_wJCM_SvB_FvT.txt -o root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/UL/  -p NONE  -y 2017 --bTag 0.6  --bTagSF -l 36.7e3 --isMC  --histFile hists_4b_wFvT_Nominal.root --histDetailLevel fourTag.passMDRs.passMjjOth.HHSR.passSvB --jcmNameLoad Nominal -r --FvTName FvT_Nominal


# where:
#   *TT* is [TTTo2L2Nu2016_postVFP, TTTo2L2Nu2016_preVFP, TTTo2L2Nu2017, TTTo2L2Nu2018,] x (TTToHadronic and TTToSemiLeptonic)
