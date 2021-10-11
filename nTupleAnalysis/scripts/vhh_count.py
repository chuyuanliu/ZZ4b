import ROOT
import vhh_fileHelper as fh
import math
ROOT.gROOT.SetBatch(True)

inputPath = "/uscms/home/chuyuanl/nobackup/VHH/"

year = "17+18"
filenames = []
# couplings = fh.getCouplingList("C2V:2_0")
# for cp in couplings:
#     filenames.append(cp[2]+year+'/hists.root')
# couplings = fh.getCouplingList("C2V:10_0;C3:10_0")
# for cp in couplings:
#     filenames.append('couplings/'+cp[2]+year+'.root')
hist = '/hists_j.root'
tag = 'threeTag'
filenames.append('data'+year)
filenames.append('TT'+year)

regions = ['SB', 'CR', 'HHSB', 'HHCR']
file={}
count = {}
for filename in filenames:
    file[filename]={}
    count[filename]={}
    inFile =ROOT.TFile(inputPath+filename + hist)
    for region in regions:
        TH1F = inFile.Get('passNjOth/'+tag+'/mainView/'+region +'/nSelJets')
        count[filename][region]=TH1F.Integral(0,16)

    
    # count['S/B'+year][cut]=count['signal'+year][cut]/count['background'+year][cut]
    # count['S/sqrt{B}'+year][cut]=count['signal'+year][cut]/math.sqrt(count['background'+year][cut])

print(hist)
print(tag)
for filename in filenames:#,'S/B','S/sqrt{B}','signal']:
    print(filename)
    for region in regions:
        print(region.ljust(20)+'%.3g' % count[filename][region])