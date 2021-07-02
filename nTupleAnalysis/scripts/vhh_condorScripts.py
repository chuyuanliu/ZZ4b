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
parser.add_option('--cp', action="store_true", dest = 'copy', default =  False, help = 'copy histograms to lpc')
parser.add_option('--hadd', action="store_true", dest = 'hadd', default =  False, help = 'hadd hists')
o, a = parser.parse_args()

hist = '/hists.root'

signals = []
if o.signal:
    signals = fh.getCouplingList(',CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0')

datas = {'2016': '',
         '2017': '',
         '2018': ''}
if o.data:
    datas = {'2016': 'BCDEFGH',
             '2017': 'BCDEF',
             '2018': 'ABCD'}

tts = []
if o.ttbar:
    tts = ['TTTo2L2Nu']#, 'TTToHadronic', 'TTToSemiLeptonic']

years = ['2017','2018']

def condorDir(dir):
    return '/store/user/' + USER + '/condor/' + dir
def LPCDir(dir):
    return '/uscms/home/' + USER + '/nobackup/' + dir
def eosmv(src, dest):
    os.system('eos root://cmseos.fnal.gov mv ' + condorDir(src) + ' ' + condorDir(dest)) 
def eosmkdir(dir):
    os.system('eos root://cmseos.fnal.gov mkdir ' + condorDir(dir))
def eosrm(dir):
    os.system('eos root://cmseos.fnal.gov rm -rf ' + condorDir(dir))
def xrdcp(src,dest):
    os.system('xrdcp -f root://cmseos.fnal.gov/' + condorDir(src) + ' ' + LPCDir(dest))
def hadd(srcs,dest):
    if len(srcs) > 0:
        print('hadd '+dest)
        cmd = 'hadd -f ' + LPCDir(dest)
        for src in srcs:
            cmd += ' ' + LPCDir(src)
        cmd += ' > hadd.log 2>&1'
        os.system(cmd)


def moveSkims():
    tag = '_b0p3'
    oldAOD = '/picoAOD' + tag + '.root'
    newAOD = '/picoAOD.root'
    for year in years:
        for cps in signals:
            for cp in cps[0:2]:
                eosmkdir('VHH/'+cp+year)
                eosmv('VHHSkims/'+cp+year+oldAOD,'VHH/'+cp+year+newAOD)
        for tt in tts:
            eosmkdir('VHH/'+tt+year)
            eosmv('skims/'+tt+year+oldAOD,'VHH/'+tt+year+newAOD)
        for data in datas[year]:
            eosmkdir('VHH/data'+year+data)
            eosmv('skims/data'+year+data+oldAOD,'VHH/data'+year+data+newAOD)

def copyToLPC():
    cpYears = copy(years)
    if '2017' in cpYears and '2018' in cpYears:
        cpYears.append('17+18')
    for year in cpYears:
        for cps in signals:
            for cp in cps[0:3]:
                hist = 'VHH/'+cp+year+'/hists.root'
                print(hist)
                xrdcp(hist, hist)

def haddLocal():
    for year in years:
        for cps in signals:
            hadd(['VHH/'+cp+year+hist for cp in cps[0:2]], 'VHH/'+cps[2]+year+hist)
        hadd(['VHH/'+tt+year+hist for tt in tts], 'VHH/TT'+year+hist)
        hadd(['VHH/data'+year+data for data in datas[year]], 'VHH/data'+year+hist)
    if '2017' in years and '2018' in years:
        haddYears = ['2017','2018']
        for cps in signals:
            for cp in cps[0:3]:
                hadd(['VHH/'+cp+year+hist for year in haddYears], 'VHH/'+cp+'17+18'+hist)
        if o.ttbar:
            hadd(['VHH/TT'+year+hist for year in haddYears], 'VHH/TT17+18'+hist)
        if o.data:
            hadd(['VHH/data'+year+hist for year in haddYears], 'VHH/data17+18'+hist)
    
if o.move:
    moveSkims()
if o.copy:
    copyToLPC()
if o.hadd:
    haddLocal()
