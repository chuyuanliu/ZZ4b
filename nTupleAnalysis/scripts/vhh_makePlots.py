import sys
import time
import collections
sys.path.insert(0, 'PlotTools/python/') #https://github.com/patrickbryant/PlotTools
import PlotTools
from ROOT import TFile
sys.path.insert(0, 'nTupleAnalysis/python/') #https://github.com/patrickbryant/nTupleAnalysis
from commandLineHelpers import *
import optparse
import vhh_fileHelper as fh

CMSSW = getCMSSW()
USER = getUSER()
EOSOUTDIR = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/"
CONDOROUTPUTBASE = "/store/user/"+USER+"/condor/"
TARBALL   = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/"+CMSSW+".tgz"

class nameTitle:
    def __init__(self, name, title):
        self.name  = name
        self.title = title

parser = optparse.OptionParser()
parser.add_option('-d', '--debug',                dest="debug",         action="store_true", default=False, help="debug")
parser.add_option('-y', '--year',                 dest="year",          default="2018", help="Year specifies trigger (and lumiMask for data)")
parser.add_option('-l', '--lumi',                 dest="lumi",          default="1",    help="Luminosity for MC normalization: units [pb]")
parser.add_option('-i', '--inputBase',            dest="inputBase",    default="None", help="Base path for where to get raw histograms")
parser.add_option('-o', '--outputBase',           dest="outputBase",    default="/uscms/home/"+USER+"/nobackup/VHH/", help="Base path for storing output plots")
parser.add_option('-p', '--plotDir',              dest="plotDir",       default="plots/", help="Base path for storing output plots")
parser.add_option('-j',            action="store_true", dest="useJetCombinatoricModel",       default=False, help="make plots after applying jetCombinatoricModel")
parser.add_option('-r',            action="store_true", dest="reweight",       default=False, help="make plots after reweighting by FvTWeight")
parser.add_option('-a',            action="store_true", dest="doAccxEff",      default=False, help="Make Acceptance X Efficiency plots")
parser.add_option('-m',            action="store_true", dest="doMain",      default=False, help="Make main plots")
parser.add_option('--data',        default=None, help="data file override")
parser.add_option('--TT',          default=None, help="TT file override")
parser.add_option('--qcd',         default=None, help="qcd file override")
parser.add_option('--doJECSyst',   action="store_true", dest="doJECSyst",      default=False, help="plot JEC variations")
parser.add_option('--coupling ',   dest = 'coupling', default = ',CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0', help = 'change signal coupling')

o, a = parser.parse_args()

#make sure outputBase ends with /
outputBase = o.outputBase + ("" if o.outputBase[-1] == "/" else "/")
inputBase = outputBase
if o.inputBase != "None":
    inputBase = o.inputBase + ("" if o.inputBase[-1] == "/" else "/")
    
outputPlot = outputBase+o.plotDir + ("" if o.plotDir[-1] == "/" else "/")
print "Plot output:",outputPlot

lumi = float(o.lumi)/1000

# VHH Files
if o.coupling == "None":
    couplings = []
else:
    couplings = fh.getCouplingList(o.coupling)

# Jet Combinatoric Model
gitRepoBase= 'ZZ4b/nTupleAnalysis/weights/'
JCMRegion = "SB"
JCMVersion = "00-00-02"
def jetCombinatoricModel(year):
    return gitRepoBase+"data"+year+"/jetCombinatoricModel_"+JCMRegion+"_"+JCMVersion+".txt"

jcm = PlotTools.read_parameter_file(jetCombinatoricModel('RunII'))
mu_qcd = jcm['mu_qcd_passMDRs']

files = {"data"+o.year  : inputBase+"data"+o.year+"/hists"+("_j" if o.useJetCombinatoricModel else "")+("_r" if o.reweight else "")+".root",
         "TT"+o.year : inputBase+"TT"+o.year+"/hists"+("_j" if o.useJetCombinatoricModel else "")+("_r" if o.reweight else "")+".root",
         }
for coupling in couplings:
    filename = coupling[2]+o.year
    files[filename] = inputBase + filename + "/hists.root"
if not o.reweight:
    files["qcd"+o.year] = inputBase+"qcd"+o.year+"/hists"+("_j" if o.useJetCombinatoricModel else "")+".root"

#
#  Command Line overrides
#
if o.data is not None:
    print "Using data file",o.data
    files["data"+o.year] = o.data

# if o.qcd is not None:
#     print "Using qcd file",o.qcd
#     files["qcd"+o.year] = o.qcd

if o.TT is not None:
    print "Using TT file",o.TT
    files["TT"+o.year] = o.TT

for sample in files:
    files[sample] = TFile.Open(files[sample])

JECSysts = [nameTitle("_jerUp", "JER Up"), nameTitle("_jerDown", "JER Down"),
            nameTitle("_jesTotalUp", "JES Up"), nameTitle("_jesTotalDown", "JES Down")]


# DiJet Mass Plane Region Definitions
leadStBias = 1.02  # leading st dijet mass peak is shifted up by a few percent
sublStBias = 0.98  # sub-leading st dijet mass peak is shifted down by a few percent
mZ =  91.0 
mH = 125.0 
leadH = mH * leadStBias
sublH = mH * sublStBias
leadZ = mZ * leadStBias
sublZ = mZ * sublStBias

xMaxZZSR =  2.60 
rMaxZZCR = 28.00 
sZZCR =  1.01 
rMaxZZSB = 40.00 
sZZSB =  1.02 

xMaxZHSR =  1.90 
rMaxZHCR = 30.00 
sZHCR =  1.04 
rMaxZHSB = 45.00 
sZHSB =  1.06 

xMaxHHSR =  1.90 
rMaxHHCR = 30.00 
sHHCR =  1.04 
rMaxHHSB = 45.00 
sHHSB =  1.06 

SRs = [["(((x-"+str(leadH)+")/(0.1*x))**2 +((y-"+str(sublH)+")/(0.1*y))**2)", 0,250,0,250,[xMaxHHSR**2],"ROOT.kRed",     7],
       ["(((x-"+str(leadH)+")/(0.1*x))**2 +((y-"+str(sublZ)+")/(0.1*y))**2)", 0,250,0,250,[xMaxZHSR**2],"ROOT.kRed",     7],
       ["(((x-"+str(leadZ)+")/(0.1*x))**2 +((y-"+str(sublH)+")/(0.1*y))**2)", 0,250,0,250,[xMaxZHSR**2],"ROOT.kRed",     7],
       ["(((x-"+str(leadZ)+")/(0.1*x))**2 +((y-"+str(sublZ)+")/(0.1*y))**2)", 0,250,0,250,[xMaxZZSR**2],"ROOT.kRed",     7]]



cuts = [#nameTitle("passPreSel", "Preselection"), 
        #nameTitle("passDijetMass", "Pass m(j,j) Cuts"), 
        nameTitle("passMDRs", "Pass #DeltaR(j,j)"), 
        nameTitle("passNjOth", "#font[42]{N_{j}#geq 6}"), 
        nameTitle("passMjjOth", "#font[42]{60#leq m_{V}#leq 110}"), 
        nameTitle("passSvB", "#font[42]{SvB> 0.8}"), 
        # nameTitle("SvBOnly", "#font[42]{SvB> 0.8}"), 
        #nameTitle("passXWt", "rWbW > 3"), 
        # nameTitle("passMDCs", "Pass MDC's"), 
        # nameTitle("passDEtaBB", "|#Delta#eta| < 1.5"),
        ]
views = [#"allViews",
         "mainView",
         ]
regions = [#nameTitle("inclusive", ""),
           #nameTitle("ZH", "ZH SB+CR+SR"),
           #nameTitle("ZH_SvB_high", "ZH SB+CR+SR SvB>0.5"), nameTitle("ZH_SvB_low", "ZH SB+CR+SR SvB<0.5"),
           #nameTitle("ZHSB", "ZH Sideband"), nameTitle("ZHCR", "ZH Control Region"), nameTitle("ZHSR", "ZH Signal Region"),
           #nameTitle("ZZ", "ZZ SB+CR+SR"),
           #nameTitle("ZZ_SvB_high", "ZZ SB+CR+SR SvB>0.5"), nameTitle("ZZ_SvB_low", "ZZ SB+CR+SR SvB<0.5"),
           #nameTitle("ZZSB", "ZZ Sideband"), nameTitle("ZZCR", "ZZ Control Region"), nameTitle("ZZSR", "ZZ Signal Region"),
           #nameTitle("ZHSR", "ZH Signal Region"), nameTitle("ZZSR", "ZZ Signal Region"),
           #nameTitle("SCSR", "SB+CR+SR"),
           nameTitle("SB", "Sideband"), 
           #nameTitle("SR", "Signal Region"),
           nameTitle("CR", "Control Region"),
           nameTitle("HHSR", "HH Signal Region"),
           ]

plots=[]

class variable:
    def __init__(self, name, xTitle, yTitle = None, zTitle = None, rebin = None, divideByBinWidth = False, normalize = None, normalizeStack = None, mu_qcd=1):
        self.name   = name
        self.xTitle = xTitle
        self.yTitle = yTitle
        self.zTitle = zTitle
        self.rebin  = rebin
        self.divideByBinWidth = divideByBinWidth
        self.normalize = normalize
        self.normalizeStack = normalizeStack
        self.mu_qcd = mu_qcd

class standardPlot:
    def __init__(self, year, cut, view, region, var):
        self.samples=collections.OrderedDict()
        if o.reweight:
            multijet = "data"+year
        else:
            multijet = "qcd"+year

        for key in files.keys():
            self.samples[files[key]] = collections.OrderedDict()

        self.samples[files[  "data"+year]][cut.name+"/fourTag/"+view+"/"+region.name+"/"+var.name] = {
            "label" : ("Data %.1f/fb, "+year)%(lumi),
            "legend": 1,
            "isData" : True,
            "ratio" : "numer A",
            "color" : "ROOT.kBlack"}
        self.samples[files[multijet]][cut.name+"/threeTag/"+view+"/"+region.name+"/"+var.name] = {
            "label" : "Multijet Model",
            "weight": var.mu_qcd,
            "legend": 2,
            "stack" : 3,
            "ratio" : "denom A",
            "color" : "ROOT.kYellow"}
        self.samples[files["TT"+year]][cut.name+"/fourTag/"+view+"/"+region.name+"/"+var.name] = {
            "label" : "t#bar{t}",
            "legend": 3,
            "stack" : 2,
            "ratio" : "denom A",
            "color" : "ROOT.kAzure-9"}

        signalScale = 5000
        signalCount = 3
        for key in files.keys():
            if 'HHTo4B' in key:
                signalCount += 1
                couplingStr = ""
                for coupling in couplings:
                    if(coupling[3] in key):
                        couplingStr = coupling[3]
                        break
                self.samples[files[key]][cut.name+"/fourTag/"+view+"/"+region.name+"/"+var.name] = {
                "label"    : "VHH#rightarrowjjb#bar{b}b#bar{b} "+couplingStr+"(#times"+str(signalScale)+")",
                "legend"   : signalCount,
                "weight"   : signalScale,
                "color"    : str(signalCount-1)}

        self.parameters = {"titleLeft"   : "#bf{CMS} Internal",
                           "titleCenter" : region.title,
                           "titleRight"  : cut.title,
                           "maxDigits"   : 4,
                           "ratio"     : True,
                           "rMin"      : 0.5 if (not o.reweight and not o.year == "RunII") else 0.9,
                           "rMax"      : 1.5 if (not o.reweight and not o.year == "RunII") else 1.1,
                           "rTitle"    : "Data / Bkgd.",
                           "xTitle"    : var.xTitle,
                           "yTitle"    : ("Events" if view != "allViews" else "Views") if not var.yTitle else var.yTitle,
                           "outputDir" : outputPlot+"data/"+year+"/"+cut.name+"/"+view+"/"+region.name+"/",
                           "outputName": var.name}
        if var.divideByBinWidth: self.parameters["divideByBinWidth"] = True
        if var.rebin: self.parameters["rebin"] = var.rebin
        if var.normalizeStack: self.parameters["normalizeStack"] = var.normalizeStack
        if var.normalize: self.parameters["normalize"]=var.normalize
        if 'SvB' in var.name and 'SR' in region.name: self.parameters['xleg'] = [0.3, 0.3+0.33]

    def plot(self, debug=False):
        PlotTools.plot(self.samples, self.parameters, o.debug or debug)


class mcPlot:
    def __init__(self, year, cut, view, region, var):
        self.samples=collections.OrderedDict()
        self.samples[files["TT"+year]] = collections.OrderedDict()
        for key in files.keys():
            if 'HHTo4B' in key:
                self.samples[files[key]] = collections.OrderedDict()

        self.samples[files["TT"+year]][cut.name+"/threeTag/"+view+"/"+region.name+"/"+var.name] = {
            "label" : "t#bar{t} (3-tag)",
            "legend": 1,
            "ratio" : "denom A",
            "color" : "ROOT.kAzure-9"}
        self.samples[files["TT"+year]][cut.name+"/fourTag/"+view+"/"+region.name+"/"+var.name] = {
            "label" : "t#bar{t} (4-tag)",
            "drawOptions" : "PE ex0",
            "legend": 2,
            "ratio" : "numer A",
            "color" : "ROOT.kAzure-9"}

        self.samples[files["VHHTo4B_CV_1_0_C2V_1_0_C3_1_0_"+year]][cut.name+"/threeTag/"+view+"/"+region.name+"/"+var.name] = {
            "label"    : "VHH#rightarrowjjb#bar{b}b#bar{b} (3-tag #times1000)",
            "legend"   : 5,
            "ratio" : "denom C",
            "weight" : 1000,
            "color"    : "ROOT.kRed"}
        self.samples[files["VHHTo4B_CV_1_0_C2V_1_0_C3_1_0_"+year]][cut.name+"/fourTag/"+view+"/"+region.name+"/"+var.name] = {
            "label"    : "VHH#rightarrowjjb#bar{b}b#bar{b} (4-tag #times1000)",
            "drawOptions" : "PE ex0",
            "legend"   : 6,
            "ratio" : "numer C",
            "weight" : 1000,
            "color"    : "ROOT.kRed"}
    

        self.parameters = {"titleLeft"   : "#bf{CMS} Simulation Internal",
                           "titleCenter" : region.title,
                           "titleRight"  : cut.title,
                           "ratio"     : True,
                           "rMin"      : 0,
                           "rMax"      : 2,
                           "rTitle"    : "Four / Three",
                           "xTitle"    : var.xTitle,
                           "yTitle"    : ("Events" if view != "allViews" else "Views") if not var.yTitle else var.yTitle,
                           "outputDir" : outputPlot+"mc/"+year+"/"+cut.name+"/"+view+"/"+region.name+"/",
                           "outputName": var.name}
        if var.divideByBinWidth: self.parameters["divideByBinWidth"] = True
        if var.rebin: self.parameters["rebin"] = var.rebin
        if var.normalizeStack: self.parameters["normalizeStack"] = var.normalizeStack
        if var.normalize: self.parameters["normalize"]=var.normalize

    def plot(self, debug=False):
        PlotTools.plot(self.samples, self.parameters, o.debug or debug)


class JECPlot:
    def __init__(self, year, cut, view, region, var):
        self.samples=collections.OrderedDict()
        self.samples[files["VHHTo4B_CV_1_0_C2V_1_0_C3_1_0_"+year]] = collections.OrderedDict()

        self.samples[files["VHHTo4B_CV_1_0_C2V_1_0_C3_1_0_"+year]][cut.name+"/fourTag/"+view+"/"+region.name+"/"+var.name] = {
            "label"    : "WHH Nominal",
            #"drawOptions" : "HIST",
            "legend"   : 1,
            "ratio" : "denom A",
            "weight" : 1,
            "color"    : "ROOT.kRed"}

        markers = ['2','3','4','5']
        for i, JECSyst in enumerate(JECSysts):
            VHH = files["VHHTo4B_CV_1_0_C2V_1_0_C3_1_0_"+year].replace('.root', JECSyst.name+'.root')
            self.samples[VHH] = collections.OrderedDict()

            self.samples[VHH][cut.name+"/fourTag/"+view+"/"+region.name+"/"+var.name] = {
                "label"    : "VHH"+JECSyst.title,
                "drawOptions" : "PE ex0",
                "legend"   : 2*i + 2,
                "ratio" : "numer A",
                "weight" : 1,
                "marker" : markers[i],
                "color"    : "ROOT.kRed"}


        self.parameters = {"titleLeft"   : "#bf{CMS} Simulation Internal",
                           "titleCenter" : region.title,
                           "titleRight"  : cut.title,
                           "ratio"     : True,
                           "rMin"      : 0,
                           "rMax"      : 2,
                           "rTitle"    : "Syst. / Nom.",
                           "xTitle"    : var.xTitle,
                           "yTitle"    : ("Events" if view != "allViews" else "Views") if not var.yTitle else var.yTitle,
                           "outputDir" : outputPlot+"mc/"+year+"/"+cut.name+"/"+view+"/"+region.name+"/",
                           "outputName": var.name+"_JECSysts"}
        if var.divideByBinWidth: self.parameters["divideByBinWidth"] = True
        if var.rebin: self.parameters["rebin"] = var.rebin
        if var.normalizeStack: self.parameters["normalizeStack"] = var.normalizeStack
        if var.normalize: self.parameters["normalize"]=var.normalize

    def plot(self, debug=False):
        PlotTools.plot(self.samples, self.parameters, o.debug or debug)


class TH2Plot:
    def __init__(self, topDir, fileName, year, cut, tag, view, region, var, debug=False):
        self.debug = debug
        self.samples=collections.OrderedDict()

        if tag=="Background":
            if o.reweight:
                multijet = "data"+year
            else:
                multijet = "qcd"+year
            self.samples[files[ multijet]] = collections.OrderedDict()
            self.samples[files["TT"+year]] = collections.OrderedDict()

            self.samples[files[multijet]][cut.name+"/threeTag/"+view+"/"+region.name+"/"+var.name] = {"drawOptions": "COLZ",
                                                                                                      "stack" : 2}
            self.samples[files["TT"+year]][cut.name+"/fourTag/"+view+"/"+region.name+"/"+var.name] = {"drawOptions": "COLZ",
                                                                                                      "stack" : 1}
        else:
            self.samples[files[fileName.name]] = collections.OrderedDict()
            self.samples[files[fileName.name]][cut.name+"/"+tag+"/"+view+"/"+region.name+"/"+var.name] = {"drawOptions": "COLZ"}
                
        self.parameters = {"titleLeft"       : "#scale[0.7]{#bf{CMS} Internal}",
                           "titleCenter"      : "#scale[0.7]{"+region.title+"}",
                           "titleRight"      : "#scale[0.7]{"+cut.title+"}",
                           "subTitleRight"   : "#scale[0.7]{"+fileName.title+"}",
                           "yTitle"      : var.yTitle,
                           "xTitle"      : var.xTitle,
                           "zTitle"      : ("Events / Bin" if view != "allViews" else "Views / Bin"),
                           "zTitleOffset": 1.4,
                           "zMin"        : 0,
                           "maxDigits"   : 4,
                           "xNdivisions" : 505,
                           "yNdivisions" : 505,
                           "rMargin"     : 0.15,
                           "rebin"       : 1, 
                           "canvasSize"  : [720,660],
                           "outputDir"   : outputPlot+topDir+"/"+year+"/"+cut.name+"/"+view+"/"+region.name+"/",
                           "outputName"  : var.name+"_"+tag,
                           }
        self.parameters["functions"] = SRs

    def newSample(self, topDir, fileName, year, cut, tag, view, region, var):
        self.samples[files[fileName.name]] = collections.OrderedDict()
        self.samples[files[fileName.name]][cut.name+"/"+tag+"/"+view+"/"+region.name+"/"+var.name] = {"drawOptions": "COLZ"}
        self.parameters["titleCenter"]   = "#scale[0.7]{"+region.title+"}"
        self.parameters["titleRight"]    = "#scale[0.7]{"+cut.title+"}"
        self.parameters["subTitleRight"] = "#scale[0.7]{"+fileName.title+"}"
        self.parameters["outputDir"]     = outputPlot+topDir+"/"+year+"/"+cut.name+"/"+view+"/"+region.name+"/"
        self.parameters["outputName"]    = var.name+"_"+tag

    def plot(self, debug=False):
        PlotTools.plot(self.samples, self.parameters, o.debug or debug or self.debug)
        if self.debug: raw_input()


variables=[variable("nPVs", "Number of Primary Vertices"),
           variable("nPVsGood", "Number of 'Good' Primary Vertices"),
           variable("nSelJets", "Number of Selected Jets"),
           variable("nSelJets_lowSt", "Number of Selected Jets (s_{T,4j} < 320 GeV)"),
           variable("nSelJets_midSt", "Number of Selected Jets (320 < s_{T,4j} < 450 GeV)"),
           variable("nSelJets_highSt", "Number of Selected Jets (s_{T,4j} > 450 GeV)"),
           variable("nSelJetsUnweighted", "Number of Selected Jets (Unweighted)", mu_qcd=mu_qcd),
           variable("nPSTJets", "Number of Tagged + Pseudo-Tagged Jets"),
           variable("nPSTJets_lowSt", "Number of Tagged + Pseudo-Tagged Jets (s_{T,4j} < 320 GeV)"),
           variable("nPSTJets_midSt", "Number of Tagged + Pseudo-Tagged Jets (320 < s_{T,4j} < 450 GeV)"),
           variable("nPSTJets_highSt", "Number of Tagged + Pseudo-Tagged Jets (s_{T,4j} > 450 GeV)"),
           variable("nTagJets", "Number of Tagged Jets"),
           variable("nAllJets", "Number of Jets"),
           variable("st", "Scalar sum of all jet p_{T}'s [GeV]"),
           variable("stNotCan", "Scalar sum of all other jet p_{T}'s [GeV]"),
           variable("FvT", "Four vs Three Tag Classifier Output", rebin=[i/100.0 for i in range(0,45,5)]+[i/100.0 for i in range(45,55)]+[i/100.0 for i in range(55,101,5)], yTitle = "Events / 0.01 Output"),
           variable("FvT", "FvT Classifier Reweight", rebin = 2),
           variable("FvT_pd4", "FvT Regressed P(Four-tag Data)", rebin = 2),
           variable("FvT_pd3", "FvT Regressed P(Three-tag Data)", rebin = 2),
           variable("FvT_pt4", "FvT Regressed P(Four-tag t#bar{t})", rebin = 2),
           variable("FvT_pt3", "FvT Regressed P(Three-tag t#bar{t})", rebin = 2),
           variable("FvT_pm4", "FvT Regressed P(Four-tag Multijet)", rebin = 2),
           variable("FvT_pm3", "FvT Regressed P(Three-tag Multijet)", rebin = 2),
           variable("FvT_pt",  "FvT Regressed P(t#bar{t})", rebin = 2),
        #    variable("SvB_ps",  "SvB Regressed P(ZZ)+P(ZH)", rebin = 2),
        #    variable("SvB_pzz", "SvB Regressed P(ZZ)", rebin = 2),
        #    variable("SvB_pzh", "SvB Regressed P(ZH)", rebin = 2),
        #    variable("SvB_ptt", "SvB Regressed P(t#bar{t})", rebin = [0.02*i for i in range(21)]),
        #    variable("SvB_ps_zh",  "SvB Regressed P(ZZ)+P(ZH), P(ZH) #geq P(ZZ)", rebin = 2),
        #    variable("SvB_ps_zz",  "SvB Regressed P(ZZ)+P(ZH), P(ZZ) > P(ZH)", rebin = 2),
        #    variable("SvB_MA_pzz", "SvB_MA Regressed P(ZZ)", rebin = 2),
        #    variable("SvB_MA_pzh", "SvB_MA Regressed P(ZH)", rebin = 2),
        #    variable("SvB_MA_ptt", "SvB_MA Regressed P(t#bar{t})", rebin = [0.02*i for i in range(21)]),
        #    variable("SvB_MA_ps_zh",  "SvB_MA Regressed P(ZZ)+P(ZH), P(ZH) #geq P(ZZ)", rebin = 2),
        #    variable("SvB_MA_ps_zz",  "SvB_MA Regressed P(ZZ)+P(ZH), P(ZZ) > P(ZH)", rebin = 2),
        #    variable("SvB_ps_zh_0_75",  "SvB Regressed P(ZZ)+P(ZH), P(ZH) #geq P(ZZ), 0<p_{T,Z}<75", rebin = 5),
        #    variable("SvB_ps_zh_75_150",  "SvB Regressed P(ZZ)+P(ZH), P(ZH) #geq P(ZZ), 75<p_{T,Z}<150", rebin = 2),
        #    variable("SvB_ps_zh_150_250",  "SvB Regressed P(ZZ)+P(ZH), P(ZH) #geq P(ZZ), 150<p_{T,Z}<250", rebin = 2),
        #    variable("SvB_ps_zh_250_400",  "SvB Regressed P(ZZ)+P(ZH), P(ZH) #geq P(ZZ), 250<p_{T,Z}<400", rebin = 2),
        #    variable("SvB_ps_zh_400_inf",  "SvB Regressed P(ZZ)+P(ZH), P(ZH) #geq P(ZZ), 400<p_{T,Z}<inf", rebin = 5),
        #    variable("SvB_ps_zz_0_75",  "SvB Regressed P(ZZ)+P(ZH), P(ZZ) > P(ZH), 0<p_{T,Z}<75", rebin = 5),
        #    variable("SvB_ps_zz_75_150",  "SvB Regressed P(ZZ)+P(ZH), P(ZZ) > P(ZH), 75<p_{T,Z}<150", rebin = 2),
        #    variable("SvB_ps_zz_150_250",  "SvB Regressed P(ZZ)+P(ZH), P(ZZ) > P(ZH), 150<p_{T,Z}<250", rebin = 2),
        #    variable("SvB_ps_zz_250_400",  "SvB Regressed P(ZZ)+P(ZH), P(ZZ) > P(ZH), 250<p_{T,Z}<400", rebin = 2),
        #    variable("SvB_ps_zz_400_inf",  "SvB Regressed P(ZZ)+P(ZH), P(ZZ) > P(ZH), 400<p_{T,Z}<inf", rebin = 5),
        #    variable("FvT_q_score", "FvT q_score", rebin = 2),
        #    variable("SvB_q_score", "SvB q_score", rebin = 2),
        #    variable("SvB_MA_q_score", "SvB_MA q_score", rebin = 2),
           #variable("ZHvB", "ZH vs Background Output", rebin=5),
           #variable("ZZvB", "ZZ vs Background Output", rebin=5),
        #    variable("xZH", "x_{ZH}"),
        #    variable("xZZ", "x_{ZZ}"),
        #    variable("xWt0", "Minimum x_{Wt} (#geq0 not candidate jets)", rebin=1),
        #    variable("xWt1", "Minimum x_{Wt} (#geq1 not candidate jets)", rebin=1),
        #    variable("xWt2", "Minimum x_{Wt} (#geq2 not candidate jets)", rebin=1),
        #    variable("xWt",  "x_{Wt}", rebin=1),
        #    variable("t/dRbW", "Top Candidate #DeltaR(b,W)"),
        #    variable("t/m", "Top Candidate Mass [GeV]"),
        #    variable("t/pt_m", "Top Candidate p_{T} [GeV]"),
        #    variable("t/W/m", "W Boson Candidate Mass [GeV]"),
        #    variable("t/W/dR", "W Boson Candidate #DeltaR(j,j)"),
        #    variable("t/b/pt_m", "Top Candidate b p_{T} [GeV]"),
        #    variable("t/mbW", "Top Candidate m_{b,W} [GeV]"),
        #    variable("t/xWt", "Top Candidate x_{W,t}"),
        #    variable("t/xWbW", "Top Candidate x_{W,bW}"),
        #    variable("t/rWbW", "Top Candidate r_{W,bW}"),
        #    variable("t0/dRbW", "Top Candidate (#geq0 not candidate jets) #DeltaR(b,W)"),
        #    variable("t0/m", "Top Candidate (#geq0 not candidate jets) Mass [GeV]"),
        #    variable("t0/W/m", "W Boson Candidate (#geq0 not candidate jets) Mass [GeV]"),
        #    variable("t0/W/dR", "W Boson Candidate (#geq0 not candidate jets) #DeltaR(j,j)"),
        #    variable("t0/mbW", "Top Candidate (#geq0 not candidate jets) m_{b,W} [GeV]"),
        #    variable("t0/xWt", "Top Candidate (#geq0 not candidate jets) x_{W,t}"),
        #    variable("t1/dRbW", "Top Candidate (#geq1 not candidate jets) #DeltaR(b,W)"),
        #    variable("t1/m", "Top Candidate (#geq1 not candidate jets) Mass [GeV]"),
        #    variable("t1/W/m", "W Boson Candidate (#geq1 not candidate jets) Mass [GeV]"),
        #    variable("t1/W/dR", "W Boson Candidate (#geq1 not candidate jets) #DeltaR(j,j)"),
        #    variable("t1/mbW", "Top Candidate (#geq1 not candidate jets) m_{b,W} [GeV]"),
        #    variable("t1/xWt", "Top Candidate (#geq1 not candidate jets) x_{W,t}"),
           # variable("t2/dRbW", "Top Candidate (#geq2 not candidate jets) #DeltaR(b,W)"),
           # variable("t2/m", "Top Candidate (#geq2 not candidate jets) Mass [GeV]"),
           # variable("t2/W/m", "W Boson Candidate (#geq2 not candidate jets) Mass [GeV]"),
           # variable("t2/mbW", "Top Candidate (#geq2 not candidate jets) m_{b,W} [GeV]"),
           # variable("t2/xWt", "Top Candidate (#geq2 not candidate jets) x_{W,t}"),
           variable("mZH", "m_{ZH} [GeV]", divideByBinWidth = True),
           variable("mZZ", "m_{ZZ} [GeV]", divideByBinWidth = True),
           variable("dBB", "D_{BB} [GeV]"),
           variable("dEtaBB", "#Delta#eta(B_{1}, B_{2})"),
           variable("dRBB", "#DeltaR(B_{1}, B_{2})"),
           variable("v4j/m_l", "m_{4j} [GeV]"),
           variable("v4j/pt_l", "p_{T,4j} [GeV]"),
           variable("v4j/pz_l", "|p_{z,4j}| [GeV]", rebin=2),
           variable("s4j", "s_{T,4j} [GeV]"),
           variable("r4j", "p_{T,4j} / s_{T,4j}"),
           variable("m123", "m_{1,2,3} [GeV]"),
           variable("m023", "m_{0,2,3} [GeV]"),
           variable("m013", "m_{0,1,3} [GeV]"),
           variable("m012", "m_{0,1,2} [GeV]"),
           variable("canJets/pt_s", "Boson Candidate Jets p_{T} [GeV]"),
           variable("canJets/pt_m", "Boson Candidate Jets p_{T} [GeV]"),
           variable("canJets/pt_l", "Boson Candidate Jets p_{T} [GeV]"),
           variable("canJets/eta", "Boson Candidate Jets #eta"),
           variable("canJets/phi", "Boson Candidate Jets #phi"),
           variable("canJets/m",   "Boson Candidate Jets Mass [GeV]"),
           variable("canJets/m_s", "Boson Candidate Jets Mass [GeV]"),
           variable("canJets/e",   "Boson Candidate Jets Energy [GeV]"),
           variable("canJets/deepFlavB", "Boson Candidate Jets Deep Flavour B"),
           variable("canJets/deepB", "Boson Candidate Jets Deep CSV B"),
           variable("canJets/CSVv2", "Boson Candidate Jets CSVv2"),
           variable("canJets/puId", "Boson Candidate Jets Pilup ID"),
           variable("othJets/pt_s", "Other Jets p_{T} [GeV]"),
           variable("othJets/pt_m", "Other Jets p_{T} [GeV]"),
           variable("othJets/pt_l", "Other Jets p_{T} [GeV]"),
           variable("othJets/eta", "Other Jets #eta"),
           variable("othJets/phi", "Other Jets #phi"),
           variable("othJets/m",   "Other Jets Mass [GeV]"),
           variable("othJets/m_s", "Other Jets Mass [GeV]"),
           variable("othJets/e",   "Other Jets Energy [GeV]"),
           variable("othJets/deepFlavB", "Other Jets Deep Flavour B"),
           variable("othJets/deepB", "Other Jets Deep CSV B"),
           variable("othJets/CSVv2", "Other Jets CSVv2"),
           variable("othJets/puId", "Other Jets Pilup ID"),
           variable("allNotCanJets/pt_s", "All jets (p_{T}>20) excluding boson candidate jets p_{T} [GeV]"),
           variable("allNotCanJets/pt_m", "All jets (p_{T}>20) excluding boson candidate jets p_{T} [GeV]"),
           variable("allNotCanJets/pt_l", "All jets (p_{T}>20) excluding boson candidate jets p_{T} [GeV]"),
           variable("allNotCanJets/eta", "All jets (p_{T}>20) excluding boson candidate jets #eta"),
           variable("allNotCanJets/phi", "All jets (p_{T}>20) excluding boson candidate jets #phi"),
           variable("allNotCanJets/m",   "All jets (p_{T}>20) excluding boson candidate jets Mass [GeV]"),
           variable("allNotCanJets/m_s", "All jets (p_{T}>20) excluding boson candidate jets Mass [GeV]"),
           variable("allNotCanJets/e",   "All jets (p_{T}>20) excluding boson candidate jets Energy [GeV]"),
           variable("allNotCanJets/deepFlavB", "All jets (p_{T}>20) excluding boson candidate jets Deep Flavour B"),
           variable("allNotCanJets/deepB", "All jets (p_{T}>20) excluding boson candidate jets Deep CSV B"),
           variable("allNotCanJets/CSVv2", "All jets (p_{T}>20) excluding boson candidate jets CSVv2"),
           variable("allNotCanJets/puId", "All jets (p_{T}>20) excluding boson candidate jets Pileup ID"),
           variable("aveAbsEta", "Boson Candidate Jets <|#eta|>"),
           variable("aveAbsEtaOth", "Other Jets <|#eta|>"),

           variable("canJet0/pt_s", "Boson Candidate Jet_{0} p_{T} [GeV]"),
           variable("canJet0/pt_m", "Boson Candidate Jet_{0} p_{T} [GeV]"),
           variable("canJet0/pt_l", "Boson Candidate Jet_{0} p_{T} [GeV]"),
           variable("canJet0/eta", "Boson Candidate Jet_{0} #eta"),
           variable("canJet0/phi", "Boson Candidate Jet_{0} #phi"),
           variable("canJet0/deepFlavB", "Boson Candidate Jet_{0} Deep Flavour B"),
           variable("canJet0/deepB", "Boson Candidate Jet_{0} Deep CSV B"),
           variable("canJet0/CSVv2", "Boson Candidate Jet_{0} CSVv2"),

           variable("canJet1/pt_s", "Boson Candidate Jet_{1} p_{T} [GeV]"),
           variable("canJet1/pt_m", "Boson Candidate Jet_{1} p_{T} [GeV]"),
           variable("canJet1/pt_l", "Boson Candidate Jet_{1} p_{T} [GeV]"),
           variable("canJet1/eta", "Boson Candidate Jet_{1} #eta"),
           variable("canJet1/phi", "Boson Candidate Jet_{1} #phi"),
           variable("canJet1/deepFlavB", "Boson Candidate Jet_{1} Deep Flavour B"),
           variable("canJet1/deepB", "Boson Candidate Jet_{1} Deep CSV B"),
           variable("canJet1/CSVv2", "Boson Candidate Jet_{1} CSVv2"),

           variable("canJet2/pt_s", "Boson Candidate Jet_{2} p_{T} [GeV]"),
           variable("canJet2/pt_m", "Boson Candidate Jet_{2} p_{T} [GeV]"),
           variable("canJet2/pt_l", "Boson Candidate Jet_{2} p_{T} [GeV]"),
           variable("canJet2/eta", "Boson Candidate Jet_{2} #eta"),
           variable("canJet2/phi", "Boson Candidate Jet_{2} #phi"),
           variable("canJet2/deepFlavB", "Boson Candidate Jet_{2} Deep Flavour B"),
           variable("canJet2/deepB", "Boson Candidate Jet_{2} Deep CSV B"),
           variable("canJet2/CSVv2", "Boson Candidate Jet_{2} CSVv2"),

           variable("canJet3/pt_s", "Boson Candidate Jet_{3} p_{T} [GeV]"),
           variable("canJet3/pt_m", "Boson Candidate Jet_{3} p_{T} [GeV]"),
           variable("canJet3/pt_l", "Boson Candidate Jet_{3} p_{T} [GeV]"),
           variable("canJet3/eta", "Boson Candidate Jet_{3} #eta"),
           variable("canJet3/phi", "Boson Candidate Jet_{3} #phi"),
           variable("canJet3/deepFlavB", "Boson Candidate Jet_{3} Deep Flavour B"),
           variable("canJet3/deepB", "Boson Candidate Jet_{3} Deep CSV B"),
           variable("canJet3/CSVv2", "Boson Candidate Jet_{3} CSVv2"),
           variable("leadSt/m",    "Leading S_{T} Dijet Mass [GeV]"),
           variable("leadSt/dR",   "Leading S_{T} Dijet #DeltaR(j,j)"),
           variable("leadSt/pt_m", "Leading S_{T} Dijet p_{T} [GeV]"),
           variable("leadSt/eta",  "Leading S_{T} Dijet #eta"),
           variable("leadSt/phi",  "Leading S_{T} Dijet #phi"),
           variable("sublSt/m",    "Subleading S_{T} Dijet Mass [GeV]"),
           variable("sublSt/dR",   "Subleading S_{T} Dijet #DeltaR(j,j)"),
           variable("sublSt/pt_m", "Subleading S_{T} Dijet p_{T} [GeV]"),
           variable("sublSt/eta",  "Subleading S_{T} Dijet #eta"),
           variable("sublSt/phi",  "Subleading S_{T} Dijet #phi"),
           variable("leadM/m",    "Leading Mass Dijet Mass [GeV]"),
           variable("leadM/dR",   "Leading Mass Dijet #DeltaR(j,j)"),
           variable("leadM/pt_m", "Leading Mass Dijet p_{T} [GeV]"),
           variable("leadM/eta",  "Leading Mass Dijet #eta"),
           variable("leadM/phi",  "Leading Mass Dijet #phi"),
           variable("sublM/m",    "Subleading Mass Dijet Mass [GeV]"),
           variable("sublM/dR",   "Subleading Mass Dijet #DeltaR(j,j)"),
           variable("sublM/pt_m", "Subleading Mass Dijet p_{T} [GeV]"),
           variable("sublM/eta",  "Subleading Mass Dijet #eta"),
           variable("sublM/phi",  "Subleading Mass Dijet #phi"),
           variable("lead/m",    "Leading P_{T} Dijet Mass [GeV]"),
           variable("lead/dR",   "Leading p_{T} Dijet #DeltaR(j,j)"),
           variable("lead/pt_m", "Leading p_{T} Dijet p_{T} [GeV]"),
           variable("lead/eta",  "Leading p_{T} Dijet #eta"),
           variable("lead/phi",  "Leading p_{T} Dijet #phi"),
           variable("subl/m",    "Subleading p_{T} Dijet Mass [GeV]"),
           variable("subl/dR",   "Subleading p_{T} Dijet #DeltaR(j,j)"),
           variable("subl/pt_m", "Subleading p_{T} Dijet p_{T} [GeV]"),
           variable("subl/eta",  "Subleading p_{T} Dijet #eta"),
           variable("subl/phi",  "Subleading p_{T} Dijet #phi"),
           variable("close/m",    "Minimum #DeltaR(j,j) Dijet Mass [GeV]"),
           variable("close/dR",   "Minimum #DeltaR(j,j) Dijet #DeltaR(j,j)"),
           variable("close/pt_m", "Minimum #DeltaR(j,j) Dijet p_{T} [GeV]"),
           variable("close/eta",  "Minimum #DeltaR(j,j) Dijet #eta"),
           variable("close/phi",  "Minimum #DeltaR(j,j) Dijet #phi"),
           variable("other/m",    "Complement of Minimum #DeltaR(j,j) Dijet Mass [GeV]"),
           variable("other/dR",   "Complement of Minimum #DeltaR(j,j) Dijet #DeltaR(j,j)"),
           variable("other/pt_m", "Complement of Minimum #DeltaR(j,j) Dijet p_{T} [G eV]"),
           variable("other/eta",  "Complement of Minimum #DeltaR(j,j) Dijet #eta"),
           variable("other/phi",  "Complement of Minimum #DeltaR(j,j) Dijet #phi"),
           #VHH
           variable("mjjOther",  "m_{V(jj)} [GeV]"),
           variable("ptjjOther",  "p_{T} of V(jj) [GeV]"),
           variable("mHH",  "m_{HH} [GeV]"),
           variable("SvB_MA_ps",  "SvB_MA Regressed P(VHH)",normalize=True),
           ]

if o.doMain:
    for cut in cuts:
        for view in views:
            for region in regions:
                for var in variables:
                    plots.append(standardPlot(o.year, cut, view, region, var))
                    # if "ZHHTo4B_CV_1_0_C2V_1_0_C3_1_0_"+o.year in files and "WHHTo4B_CV_1_0_C2V_1_0_C3_1_0_"+o.year in files:
                    #     plots.append(      mcPlot(o.year, cut, view, region, var))
                    # if o.doJECSyst and "ZHHTo4B_CV_1_0_C2V_1_0_C3_1_0_"+o.year in files and "WHHTo4B_CV_1_0_C2V_1_0_C3_1_0_"+o.year in files:
                    #     plots.append(     JECPlot(o.year, cut, view, region, var))


variables2d = [variable("leadSt_m_vs_sublSt_m", "Leading S_{T} Dijet Mass [GeV]", "Subleading S_{T} Dijet Mass [GeV]"),
               variable("leadM_m_vs_sublM_m", "Leading Mass Dijet Mass [GeV]", "Subleading Mass Dijet Mass [GeV]"),
               variable("t/mW_vs_mt", "W Boson Candidate Mass [GeV]", "Top Quark Candidate Mass [GeV]"),
               variable("t/mW_vs_mbW", "W Boson Candidate Mass [GeV]", "m_{b,W} [GeV]"),
               variable("t/mW_vs_mbW", "W Boson Candidate Mass [GeV]", "m_{b,W} [GeV]"),
               variable("t/xW_vs_xt", "x_{W}", "x_{t}"),
               variable("t/xW_vs_xbW", "x_{W}", "x_{bW}"),
               variable("t0/mW_vs_mt", "W Boson Candidate Mass [GeV]", "Top Quark Candidate Mass [GeV]"),
               variable("t0/mW_vs_mbW", "W Boson Candidate Mass [GeV]", "m_{b,W} [GeV]"),
               variable("t0/mW_vs_mbW", "W Boson Candidate Mass [GeV]", "m_{b,W} [GeV]"),
               variable("t0/xW_vs_xt", "x_{W}", "x_{t}"),
               variable("t0/xW_vs_xbW", "x_{W}", "x_{bW}"),                               
               variable("t1/mW_vs_mt", "W Boson Candidate Mass [GeV]", "Top Quark Candidate Mass [GeV]"),
               variable("t1/mW_vs_mbW", "W Boson Candidate Mass [GeV]", "m_{b,W} [GeV]"),
               variable("t1/mW_vs_mbW", "W Boson Candidate Mass [GeV]", "m_{b,W} [GeV]"),
               variable("t1/xW_vs_xt", "x_{W}", "x_{t}"),
               variable("t1/xW_vs_xbW", "x_{W}", "x_{bW}"),                               
               ]
if o.doMain:# and  False:
    for cut in cuts:
        for view in views:
            for region in regions:
                #if True:
                for var in variables2d:
                    sample = nameTitle("data"+o.year, ("Data %.1f/fb, "+o.year)%(lumi))
                    plots.append(TH2Plot("data", sample, o.year, cut, "fourTag", view, region, var))

                    sample = nameTitle(None, "Background")
                    plots.append(TH2Plot("data", sample, o.year, cut, sample.title, view, region, var, debug=False))

                    sample = nameTitle("TT"+o.year, "t#bar{t} (three-tag)")
                    plots.append(TH2Plot("ttbar", sample, o.year, cut, "threeTag", view, region, var))

                    sample = nameTitle("TT"+o.year, "t#bar{t} (four-tag)")
                    plots.append(TH2Plot("ttbar", sample, o.year, cut, "fourTag", view, region, var))


# cuts = [nameTitle("passDijetMass", "Pass m(j,j)")] + cuts
# views = ["allViews"] + views
# regions = [nameTitle("inclusive", "")] + regions
if o.doMain:
    for cut in cuts:
        for view in views:
            for region in regions:
                for key in files.keys():
                    if "HHTo4B" in key:
                        for var in variables2d:
                            sample = nameTitle(key, "VHH#rightarrowjjb#bar{b}b#bar{b}")
                            plots.append(TH2Plot(key, sample, o.year, cut, "fourTag", view, region, var))

                        var = variable("m4j_vs_leadSt_dR", "m_{4j} [GeV]", "Leading S_{T} Boson Candidate #DeltaR(j,j)")
                        TH2 = TH2Plot(key, sample, o.year, cut, "fourTag", view, region, var)
                        TH2.parameters["functions"] = [["(360./x-0.5 - y)",100,1100,0,5,[0],"ROOT.kRed",1],
                                                    ["(650./x+0.5 - y)",100,1100,0,5,[0],"ROOT.kRed",1]]
                        plots.append(TH2)

                        var = variable("m4j_vs_sublSt_dR", "m_{4j} [GeV]", "Subleading S_{T} Boson Candidate #DeltaR(j,j)")
                        TH2 = TH2Plot(key, sample, o.year, cut, "fourTag", view, region, var)
                        TH2.parameters["functions"] = [["(235./x     - y)",100,1100,0,5,[0],"ROOT.kRed",1],
                                                    ["(650./x+0.7 - y)",100,1100,0,5,[0],"ROOT.kRed",1]]
                        plots.append(TH2)

                        var = variable("m4j_vs_nViews", "m_{4j} [GeV]", "Number of Event Views")
                        TH2 = TH2Plot(key, sample, o.year, cut, "fourTag", view, region, var)
                        del TH2.parameters["functions"]
                        TH2.parameters['yMin'], TH2.parameters['yMax'] = 0.5, 3.5
                        TH2.parameters["yNdivisions"] = 003
                        plots.append(TH2)

files={}
for coupling in couplings:
    filename = coupling[2]+o.year
    files[filename] = inputBase + filename + "/hists.root"

class accxEffPlot:
    def __init__(self, topDir, fileName, year, region, denominator = nameTitle('all', ''), tag='_fourTag'):
        self.samplesAbs=collections.OrderedDict()
        self.samplesAbs[files[fileName.name].replace("hists.root","accxEff.root")] = collections.OrderedDict()
        self.samplesAbs[files[fileName.name].replace("hists.root","accxEff.root")]["jetMultiplicity_over_"+denominator.name+tag] = {
            "label"      : "#geq4 jets",
            "legend"     : 1,
            "color"      : "ROOT.kBlack",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesAbs[files[fileName.name].replace("hists.root","accxEff.root")]["bTags_over_"+denominator.name+tag] = {
            "label"      : "#geq4 b-tagged jets" if tag=='_fourTag' else "3 loose b-tags",
            "legend"     : 2,
            "color"      : "ROOT.kViolet",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesAbs[files[fileName.name].replace("hists.root","accxEff.root")]["MDRs_over_"+denominator.name+tag] = {
            "label"      : "#DeltaR(j,j)",
            "legend"     : 3,
            "color"      : "ROOT.kOrange-3",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesAbs[files[fileName.name].replace("hists.root","accxEff.root")]["NjOth_over_"+denominator.name+tag] = {
            "label"      : "#geq6 jets",
            "legend"     : 4,
            "color"      : "ROOT.kCyan",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesAbs[files[fileName.name].replace("hists.root","accxEff.root")]["MjjOth_over_"+denominator.name+tag] = {
            "label"      : "m_{V(jj)}",
            "legend"     : 5,
            "color"      : "ROOT.kGreen-3",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesAbs[files[fileName.name].replace("hists.root","accxEff.root")]["SvB_over_"+denominator.name+tag] = {
            "label"      : "SvB>0.8",
            "legend"     : 6,
            "color"      : "ROOT.kYellow",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesAbs[files[fileName.name].replace("hists.root","accxEff.root")]["SvB_HHSR_over_"+denominator.name+tag] = {
            "label"      : "SR",
            "legend"     : 7,
            "color"      : "ROOT.kBlue",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesAbs[files[fileName.name].replace("hists.root","accxEff.root")]["SvB_HHSR_HLT_over_"+denominator.name+tag] = {
            "label"      : "Trigger",
            "legend"     : 8,
            "color"      : "ROOT.kRed",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}

        self.parametersAbs = {"titleLeft"       : "#scale[0.7]{#bf{CMS} Simulation Internal}",
                              "titleCenter"      : "#scale[0.7]{"+denominator.title+"}",
                              "titleRight"   : "#scale[0.7]{"+fileName.title+"}",
                              "yTitle"     : "Acceptance #times Efficiency",
                              "xTitle"     : "True m_{4b} [GeV]",
                              "xTitleOffset": 0.95,
                              "legendTextSize":0.03,
                              "legendColumns":2,
                              "canvasSize" : [600,500],
                              "rMargin"    : 0.05,
                              "lMargin"    : 0.12,
                              "yTitleOffset": 1.1,
                              "xMin" :  250,
                              "xMax" : 2000,
                              "yMin"       : 0.00002,
                              "yMax"       : 20,
                              "xleg"       : [0.15,0.71],
                              "yleg"       : [0.77,0.92],
                              "labelSize"  : 16,
                              "logY"       : True,
                              "outputDir"   : outputPlot+topDir+"/"+year+"/",
                              "outputName" : "absoluteAccxEff"+tag,
                              }

        self.samplesRel=collections.OrderedDict()
        self.samplesRel[files[fileName.name].replace("hists.root","accxEff.root")] = collections.OrderedDict()
        self.samplesRel[files[fileName.name].replace("hists.root","accxEff.root")]["bTags_over_jetMultiplicity"+tag] = {
            "label"      : "#geq4 b-tags / #geq4 jets" if tag=='_fourTag' else "3 loose b-tags / #geq4 jets",
            "legend"     : 1,
            "color"      : "ROOT.kViolet",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesRel[files[fileName.name].replace("hists.root","accxEff.root")]["MDRs_over_bTags"+tag] = {
            "label"      : "#DeltaR(j,j) / #geq4 b-tags",
            "legend"     : 2,
            "color"      : "ROOT.kOrange-3",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesRel[files[fileName.name].replace("hists.root","accxEff.root")]["NjOth_over_MDRs"+tag] = {
            "label"      : "#geq6 jets / #DeltaR(j,j)",
            "legend"     : 3,
            "color"      : "ROOT.kCyan",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesRel[files[fileName.name].replace("hists.root","accxEff.root")]["MjjOth_over_NjOth"+tag] = {
            "label"      : "m_{V(jj)} / #geq6 jets",
            "legend"     : 4,
            "color"      : "ROOT.kGreen-3",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesRel[files[fileName.name].replace("hists.root","accxEff.root")]["SvB_over_MjjOth"+tag] = {
            "label"      : "SvB/m_{V(jj)}",
            "legend"     : 5,
            "color"      : "ROOT.kYellow",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesRel[files[fileName.name].replace("hists.root","accxEff.root")]["SvB_HHSR_over_SvB"+tag] = {
            "label"      : "SR / SvB",
            "legend"     : 6,
            "color"      : "ROOT.kBlue",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}
        self.samplesRel[files[fileName.name].replace("hists.root","accxEff.root")]["SvB_HHSR_HLT_over_SvB_HHSR"+tag] = {
            "label"      : "Trigger / SR",
            "legend"     : 7,
            "color"      : "ROOT.kRed",
            "drawOptions" : "HIST PC",
            "marker"      : "20"}

        self.parametersRel = {"titleLeft"       : "#scale[0.7]{#bf{CMS} Simulation Internal}",
                              #"titleCenter"      : "#scale[0.7]{"+region.title+"}",
                              #"titleRight"      : "#scale[0.7]{"+cut.title+"}",
                              "titleRight"   : "#scale[0.7]{"+fileName.title+"}",
                              "yTitle"     : "Acceptance #times Efficiency",
                              "xTitle"     : "True m_{4b} [GeV]",
                              "xTitleOffset": 0.95,
                              "legendTextSize":0.03,
                              "legendColumns":2,
                              "canvasSize" : [600,500],
                              "rMargin"    : 0.05,
                              "lMargin"    : 0.12,
                              "yTitleOffset": 1.1,
                              "xMin" :  250,
                              "xMax" : 2000,
                              "yMin"       : 0.0,
                              "yMax"       : 1.3,
                              "xleg"       : [0.15,0.71],
                              "yleg"       : [0.77,0.92],
                              "labelSize"  : 16,
                              "logY"       : False,
                              "drawLines"  : [[250,1,2000,1]],
                              "outputDir"   : outputPlot+topDir+"/"+year+"/",
                              "outputName" : "relativeAccxEff"+tag,
                              }
    
    def plot(self, debug = False):
        PlotTools.plot(self.samplesAbs, self.parametersAbs, o.debug or debug)
        PlotTools.plot(self.samplesRel, self.parametersRel, o.debug or debug)





if o.doAccxEff:
    for key in files.keys():
        if 'TT' not in key and 'data' not in key:
            fileName = nameTitle(key, "WHH, ZHH#rightarrowjjb#bar{b}b#bar{b}")
            region = nameTitle("HHSR", "HHSR")
            plots.append(accxEffPlot(key, fileName, o.year, region))
            plots.append(accxEffPlot(key, fileName, o.year, region, tag='_threeTag'))


nPlots=len(plots)
start = time.time()
for p, thisPlot in enumerate(plots):
    thisPlot.plot()
    elapsedTime = time.time()-start
    sys.stdout.write("\rMade %4d of %4d | %4.1f plots/sec | %3.0f%%"%(p+1, nPlots, (p+1)/elapsedTime, 100.0*(p+1)/nPlots))
    sys.stdout.flush()
print
