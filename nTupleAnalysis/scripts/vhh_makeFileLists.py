import vhh_fileHelper as fh
import os

nanoAODs = {
    '2016_preVFP':'TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODAPVv2-106X_mcRun2_asymptotic_preVFP_v9-v{:d}/NANOAODSIM',
    '2016_postVFP':'TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v{:d}/NANOAODSIM',
    '2017':'TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v{:d}/NANOAODSIM',
    '2018':'TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v{:d}/NANOAODSIM'
}
# outputPath = '/uscms/home/chuyuanl/nobackup/CMSSW_11_1_0_pre5/src/ZZ4b/fileLists/'
outputPath = '/uscms/home/chuyuanl/nobackup/CMSSW_11_1_0_pre5/src/fileLists/'

years = ['2016_preVFP', '2016_postVFP', '2017', '2018']
couplings = fh.getCouplingList(',CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0,C3:20_0')
maxVer = 10

for year in years:
    for processes in couplings:
        for process in processes[0:2]:
            files = ''
            ver = 1
            while len(files) == 0 and ver < maxVer:
                nanoAOD = '/' + process + nanoAODs[year]
                cmd = ('dasgoclient -query="file dataset=' + nanoAOD + '"').format(ver)
                print(cmd)
                files = os.popen(cmd).read()
                if len(files) != 0:
                    files = files.replace('/store/mc/', 'root://cmsxrootd.fnal.gov//store/mc/')
                    fileList =  open(outputPath + process+year + '.txt', 'w')
                    fileList.write('### ' + cmd + '\n' + files)
                    fileList.close()
                ver += 1

