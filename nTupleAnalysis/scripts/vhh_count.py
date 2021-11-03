import ROOT
import vhh_fileHelper as fh
import math
ROOT.gROOT.SetBatch(True)

inputPath = "/uscms/home/chuyuanl/nobackup/VHH/"

year = "17+18"
filenames = []
couplings = fh.getCouplingList(",CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0")
for cp in couplings:
    filenames.append(cp[2]+year+'/hists.root')
hist = '/hists_j.root'
tag = 'fourTag'
filenames.append('data'+year)
filenames.append('TT'+year)

regions = ['HHSR']#,'SB', 'CR', 'HHSB', 'HHCR']
file={}
count = {}
for filename in filenames:
    file[filename]={}
    count[filename]={}
    
for filename in filenames:#,'S/B','S/sqrt{B}','signal']:
    print(filename)
    for region in regions:
        print(region.ljust(20)+'%.3g' % count[filename][region])