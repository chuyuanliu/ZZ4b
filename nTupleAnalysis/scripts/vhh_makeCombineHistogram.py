import ROOT
import vhh_fileHelper as fh
ROOT.gROOT.SetBatch(True)

inputPath = "/uscms/home/chuyuanl/nobackup/VHH/"
#outputPath = inputPath+"couplings/combine_hists.root"
outputPath = inputPath+"couplings/combine_hists_SvB.root"
year = "17+18"
mcCouplings = []
for cp in fh.getCouplingList(",CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0"):
    mcCouplings.append(cp[2])
couplings = ",CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0,C2V:6_0;C3:8_0,C2V:6_0;C3:10_0,C2V:8_0;C3:8_0,C2V:10_0;C3:10_0"
#cut = "passMjjOth"
cut = "passSvB"
histogram = "mainView/HHSR/v4j/pt_m"

inputFiles = [["data","multijet_background"],["TT","ttbar_background"]]
for cp in fh.getCouplingList(couplings):
    inputFiles.append([cp[2],cp[2][:-1].replace('C3', 'kl')])

outputFile = ROOT.TFile(outputPath,'recreate')

for filename in inputFiles:
    if filename[0] == "data" or filename[0]=="TT":
        inFile = ROOT.TFile(inputPath+filename[0]+year+"/hists_j_r.root")
    elif filename[0] in mcCouplings:
        inFile = ROOT.TFile(inputPath+filename[0]+year+"/hists.root")
    else:
        inFile = ROOT.TFile(inputPath+"couplings/"+filename[0]+year+".root")
    hist = inFile.Get("/"+cut+"/"+("threeTag" if filename[0]=="data" and "background" in filename[1] else "fourTag")+"/"+histogram).Clone()
    hist.SetNameTitle(filename[1],filename[1]+"_"+year)
    outputFile.cd()
    hist.Write()
    inFile.Close()

outputFile.Close()