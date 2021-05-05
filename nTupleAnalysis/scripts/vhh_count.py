import ROOT
import vhh_fileHelper as fh
import math
ROOT.gROOT.SetBatch(True)

inputPath = "/uscms/home/chuyuanl/nobackup/VHH/"

year = "17+18"
filenames = []
couplings = fh.getCouplingList("C2V:2_0")
for cp in couplings:
    filenames.append(cp[2]+year+'/hists.root')
# couplings = fh.getCouplingList("C2V:10_0;C3:10_0")
# for cp in couplings:
#     filenames.append('couplings/'+cp[2]+year+'.root')
filenames.append('data'+year+'/hists_j_r.root')
filenames.append('TT'+year+'/hists_j_r.root')

cuts=["all",
      #"jetMultiplicity",
      "bTags",
      #"DijetMass",
      "MDRs",
      "NjOth",
      "MjjOth",
      "SvB",
      "SvB_HHSR",
      "SvB_HHSR_HLT"
      ]
count={}
for filename in filenames:
    count[filename]={}
    if 'data' in filename:
        tag = 'threeTag'
    else:
        tag = 'fourTag'
    inFile =ROOT.TFile(inputPath+filename)
    TH1F= inFile.Get('cutflow/'+tag+'/weighted')
    Axis = TH1F.GetXaxis()
    for cut in cuts:
        count[filename][cut]=TH1F[Axis.FindBin(cut)]

count['background'+year]={}
count['S/B'+year]={}
count['S/sqrt{B}'+year]={}
count['signal'+year]=count[couplings[0][2]+year+'/hists.root']
for cut in cuts:
    count['background'+year][cut]=count['data'+year+'/hists_j_r.root'][cut]+count['TT'+year+'/hists_j_r.root'][cut]
    count['S/B'+year][cut]=count['signal'+year][cut]/count['background'+year][cut]
    count['S/sqrt{B}'+year][cut]=count['signal'+year][cut]/math.sqrt(count['background'+year][cut])

for file in ['background','S/B','S/sqrt{B}','signal']:
    print(file)
    for cut in cuts:
        print(cut.ljust(20)+'%.3g' % count[file+year][cut])