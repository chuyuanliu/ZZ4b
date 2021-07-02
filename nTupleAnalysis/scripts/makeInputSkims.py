
import sys
sys.path.insert(0, 'nTupleAnalysis/python/') #https://github.com/patrickbryant/nTupleAnalysis
from commandLineHelpers import *
import optparse

parser = optparse.OptionParser()
parser.add_option('-e',            action="store_true", dest="execute",        default=False, help="Execute commands. Default is to just print them")
parser.add_option('-y',                                 dest="year",      default="2018,2017,2016", help="Year or comma separated list of years")
parser.add_option('--makeSkims',  action="store_true",      help="Make input skims")
parser.add_option('--copySkims',  action="store_true",      help="Make input skims")
parser.add_option('--makeSignalSkims',  action="store_true",      help="Make input skims")
parser.add_option('--makeVHHSkims',  action="store_true",      help="Make input skims")
parser.add_option('--copyToEOS',  action="store_true",      help="Copy to EOS")
parser.add_option('--cleanPicoAODs',  action="store_true",      help="rm local picoAODs")
parser.add_option('--makeInputFileLists',  action="store_true",      help="make Input file lists")
parser.add_option('--makeSignalFileLists',  action="store_true",      help="make Input file lists")
parser.add_option('--noData',       action="store_true",      help="Skip data")
parser.add_option('--noTT',       action="store_true",      help="Skip TTbar")
parser.add_option('-c',   '--condor',   action="store_true", default=False,           help="Run on condor")
parser.add_option('--debug',   action="store_true", default=False,           help="Enable debug")
parser.add_option('--email',            default=None,      help="")
parser.add_option('--bTag',   default='0.3',           help="change b-tagging working point")

o, a = parser.parse_args()

doRun = o.execute

from condorHelpers import *

CMSSW = getCMSSW()
USER = getUSER()
EOSOUTDIR = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/nominal/"
TARBALL   = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/"+CMSSW+".tgz"

def getOutDir():
    if o.condor:
        return EOSOUTDIR
    return outputDir


if o.condor:
    print "Making Tarball"
    makeTARBALL(o.execute)


#
# In the following "3b" refers to 3b subsampled to have the 4b statistics
#
#outputDir="/uscms/home/jda102/nobackup/HH4b/CMSSW_11_1_3/src/closureTests/nominal/"
outputDir="/uscms/home/"+USER+"/nobackup/VHH/"


# Helpers
runCMD='nTupleAnalysis ZZ4b/nTupleAnalysis/scripts/nTupleAnalysis_cfg.py'

years = o.year.split(",")

yearOpts = {}
yearOpts["2018"]=' -y 2018 --bTag 0.3 '
yearOpts["2017"]=' -y 2017 --bTag 0.3 '
yearOpts["2016"]=' -y 2016 --bTag 0.3 '


MCyearOpts = {}
MCyearOpts["2018"]=yearOpts["2018"]+' --bTagSF -l 60.0e3 --isMC '
MCyearOpts["2017"]=yearOpts["2017"]+' --bTagSF -l 36.7e3 --isMC '
MCyearOpts["2016"]=yearOpts["2016"]+' --bTagSF -l 35.9e3 --isMC '


dataPeriods = {}
# All
dataPeriods["2018"] = ["A","B","C","D"]
dataPeriods["2017"] = ["C","D","E","F"]
dataPeriods["2016"] = ["B","C","D","E","F","G","H"]
# for skimming 
# dataPeriods["2018"] = []
# dataPeriods["2017"] = []
# dataPeriods["2016"] = []

# for skimming
ttbarSamplesByYear = {}
ttbarSamplesByYear["2018"] = ["TTToHadronic","TTToSemiLeptonic","TTTo2L2Nu"]
ttbarSamplesByYear["2017"] = ["TTToHadronic","TTToSemiLeptonic","TTTo2L2Nu"]
ttbarSamplesByYear["2016"] = ["TTToHadronic","TTToSemiLeptonic","TTTo2L2Nu"]
# ttbarSamplesByYear["2018"] = []
# ttbarSamplesByYear["2017"] = []
#ttbarSamplesByYear["2016"] = []


eosls = "eos root://cmseos.fnal.gov ls"
eoslslrt = "eos root://cmseos.fnal.gov ls -lrt"
eosmkdir = "eos root://cmseos.fnal.gov mkdir "

WHHSamples  = {}
ZHHSamples  = {}

WHHSamples["2017"] = [
    "WHHTo4B_CV_0_5_C2V_1_0_C3_1_0_2017",
    "WHHTo4B_CV_1_0_C2V_0_0_C3_1_0_2017",
    "WHHTo4B_CV_1_0_C2V_1_0_C3_0_0_2017",
    "WHHTo4B_CV_1_0_C2V_1_0_C3_1_0_2017",
    "WHHTo4B_CV_1_0_C2V_1_0_C3_2_0_2017",
    "WHHTo4B_CV_1_0_C2V_2_0_C3_1_0_2017",
    "WHHTo4B_CV_1_5_C2V_1_0_C3_1_0_2017",
]

ZHHSamples["2017"] = [
    "ZHHTo4B_CV_0_5_C2V_1_0_C3_1_0_2017",
    "ZHHTo4B_CV_1_0_C2V_0_0_C3_1_0_2017",
    "ZHHTo4B_CV_1_0_C2V_1_0_C3_0_0_2017",
    "ZHHTo4B_CV_1_0_C2V_1_0_C3_1_0_2017",
    "ZHHTo4B_CV_1_0_C2V_1_0_C3_2_0_2017",
    "ZHHTo4B_CV_1_0_C2V_2_0_C3_1_0_2017",
    "ZHHTo4B_CV_1_5_C2V_1_0_C3_1_0_2017",
]

WHHSamples["2018"] = [
    "WHHTo4B_CV_0_5_C2V_1_0_C3_1_0_2018",
    "WHHTo4B_CV_1_0_C2V_0_0_C3_1_0_2018",
    "WHHTo4B_CV_1_0_C2V_1_0_C3_0_0_2018",
    "WHHTo4B_CV_1_0_C2V_1_0_C3_1_0_2018",
    "WHHTo4B_CV_1_0_C2V_1_0_C3_2_0_2018",
    "WHHTo4B_CV_1_0_C2V_2_0_C3_1_0_2018",
    "WHHTo4B_CV_1_5_C2V_1_0_C3_1_0_2018",
]

ZHHSamples["2018"] = [
    "ZHHTo4B_CV_0_5_C2V_1_0_C3_1_0_2018",
    "ZHHTo4B_CV_1_0_C2V_0_0_C3_1_0_2018",
    "ZHHTo4B_CV_1_0_C2V_1_0_C3_0_0_2018",
    "ZHHTo4B_CV_1_0_C2V_1_0_C3_1_0_2018",
    "ZHHTo4B_CV_1_0_C2V_1_0_C3_2_0_2018",
    "ZHHTo4B_CV_1_0_C2V_2_0_C3_1_0_2018",
    "ZHHTo4B_CV_1_5_C2V_1_0_C3_1_0_2018",
]

VHHSamples = [WHHSamples,ZHHSamples]

if o.noTT:
    ttbarSamplesByYear = {"2016":[],"2017":[],"2018":[]}

if o.noData:
    dataPeriods = {"2016":[],"2017":[],"2018":[]}

#tagID = "b0p6"
tagID = "b"+o.bTag.replace('.','p')

#
# Make skims with out the di-jet Mass cuts
#
if o.makeSkims:

    dag_config = []
    condor_jobs = []

    for y in years:
        

        histConfig = "--histFile histsFromNanoAOD.root"
        picoOut = " -p picoAOD_"+tagID+".root "
        EOSOUTDIR = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/skims/"

        #
        #  Data
        #
        for d in dataPeriods[y]:
            cmd = runCMD+" -i ZZ4b/fileLists/data"+y+d+".txt -o "+EOSOUTDIR+  yearOpts[y] + histConfig + picoOut +" --fastSkim --noDiJetMassCutInPicoAOD" + (" --debug" if o.debug else "")
            condor_jobs.append(makeCondorFile(cmd, "None", "data"+y+d+"_"+tagID, outputDir=outputDir, filePrefix="data_"))

        #
        #  TTbar
        # 
        for tt in ttbarSamplesByYear[y]:
            cmd = runCMD+" -i ZZ4b/fileLists/"+tt+y+".txt -o "+EOSOUTDIR+  MCyearOpts[y] + histConfig + picoOut +" --fastSkim --noDiJetMassCutInPicoAOD" + (" --debug" if o.debug else "")
            condor_jobs.append(makeCondorFile(cmd, "None", tt+y+"_"+tagID, outputDir=outputDir, filePrefix="TTbar_"))

    dag_config.append(condor_jobs)
    execute("rm "+outputDir+"data_All.dag", doRun)
    execute("rm "+outputDir+"data_All.dag.*", doRun)
    execute("rm "+outputDir+"TTbar_All.dag", doRun)
    execute("rm "+outputDir+"TTbar_All.dag.*", doRun)
    dag_file = makeDAGFile("data_All.dag",dag_config, outputDir=outputDir)
    cmd = "condor_submit_dag "+dag_file
    execute(cmd, o.execute)

    if o.email: execute('echo "Subject: [make3bMix4bClosure] mixInputs  Done" | sendmail '+o.email,doRun)


    


#
# Make skims with out the di-jet Mass cuts
#
if o.makeVHHSkims:


    dag_config = []
    condor_jobs = []

    histConfig = "--histFile histsFromNanoAOD.root"
    picoOut = " -p picoAOD_"+tagID+".root "
    EOSOUTDIR = "root://cmseos.fnal.gov//store/user/"+USER+"/condor/VHHSkims/"

    
    for sample in VHHSamples:

        for y in ["2017","2018"]:
        
            for d in sample[y]:
                cmd = runCMD+" -i ZZ4b/fileLists/"+d+".txt -o "+EOSOUTDIR+  MCyearOpts[y] + histConfig + picoOut +" --fastSkim " + (" --debug" if o.debug else "")
                condor_jobs.append(makeCondorFile(cmd, "None", d+"_"+tagID, outputDir=outputDir, filePrefix="skimVHH_"))


    dag_config.append(condor_jobs)

    execute("rm "+outputDir+"skimVHH_All.dag", doRun)
    execute("rm "+outputDir+"skimVHH_All.dag.*", doRun)

    dag_file = makeDAGFile("skimVHH_All.dag",dag_config, outputDir=outputDir)
    cmd = "condor_submit_dag "+dag_file
    execute(cmd, o.execute)






if o.copyToEOS:

    def copy(fileName, subDir, outFileName):
        cmd  = "xrdcp  "+fileName+" root://cmseos.fnal.gov//store/user/johnda/closureTest/skims/"+subDir+"/"+outFileName
    
        if doRun:
            os.system(cmd)
        else:
            print cmd
    
    for y in years:
    
        for p in dataPeriods[y]:
            copy("closureTests/nominal/data"+y+p+"/picoAOD_noDiJetMjj_"+tagID+".root", "data"+y, "picoAOD_noDiJetMjj_"+tagID+"_"+y+p+".root")

        for tt in ttbarSamples:
            copy("closureTests/nominal/"+tt+y+"/picoAOD_noDiJetMjj_"+tagID+".root", tt+y, "picoAOD_noDiJetMjj_"+tagID+".root")


if o.cleanPicoAODs:
    
    def rm(fileName):
        cmd  = "rm  "+fileName
    
        if doRun: os.system(cmd)
        else:     print cmd


    for y in years:
    
        for p in dataPeriods[y]:
            rm("closureTests/nominal/data"+y+p+"/picoAOD_noDiJetMjj_"+tagID+".root")

        for tt in ttbarSamples:
            rm("closureTests/nominal/"+tt+y+"/picoAOD_noDiJetMjj_"+tagID+".root")




#
#   Make inputs fileLists
#
if o.makeInputFileLists:

    def run(cmd):
        if doRun: os.system(cmd)
        else:     print cmd


    mkdir(outputDir+"/fileLists", doExecute=doRun)

    eosDir = "root://cmseos.fnal.gov//store/user/johnda/condor/ZH4b/UL/"

    for y in years:
        fileList = outputDir+"/fileLists/data"+y+".txt"    
        run("rm "+fileList)

        for p in dataPeriods[y]:
            run("echo "+eosDir+"/data"+y+p+"/picoAOD.root >> "+fileList)


        for tt in ttbarSamplesByYear[y]:
            fileList = outputDir+"/fileLists/"+tt+".txt"    
            run("rm "+fileList)

            run("echo "+eosDir+"/"+tt+"/picoAOD.root >> "+fileList)

    

#
#  Make Hists Signal Hists
#
if o.makeSignalSkims: 

    #
    #  Make Hists
    #
    dag_config = []
    condor_jobs = []

    histConfig = " --histDetailLevel allEvents.threeTag.fourTag --histFile histsFromNanoAOD.root "
    picoOut = " -p picoAOD_noDiJetMjj_"+tagID+".root "
    outDir = " -o "+getOutDir()+" "

    for y in years:

        for sig in signalSamples:
        
            inputFile = " -i ZZ4b/fileLists/"+sig+y+".txt "
            cmd = runCMD + inputFile + outDir + MCyearOpts[y]+ histConfig + picoOut  + " --fastSkim  --noDiJetMassCutInPicoAOD "
            condor_jobs.append(makeCondorFile(cmd, "None", sig+y, outputDir=outputDir, filePrefix="skimSignal_"))


    dag_config.append(condor_jobs)
    

    execute("rm "+outputDir+"skimSignal_All.dag", doRun)
    execute("rm "+outputDir+"skimSignal_All.dag.*", doRun)

    dag_file = makeDAGFile("skimSignal_All.dag",dag_config, outputDir=outputDir)
    cmd = "condor_submit_dag "+dag_file
    execute(cmd, o.execute)
        


#
#   Make inputs fileLists
#
if o.makeSignalFileLists:

    def run(cmd):
        if doRun: os.system(cmd)
        else:     print cmd


    #mkdir(outputDir+"/fileLists", execute=doRun)

    eosDir = "root://cmseos.fnal.gov//store/user/johnda/condor/nominal/"    

    for y in years:

        for sig in signalSamples:
            fileList = outputDir+"/fileLists/"+sig+y+"_noMjj_"+tagID+".txt"    
            run("rm "+fileList)

            run("echo "+eosDir+"/"+sig+y+"/picoAOD_noDiJetMjj_"+tagID+".root >> "+fileList)


