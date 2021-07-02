import numpy as np
import vhh_fileHelper as fh
import ROOT
import re
import os
ROOT.gROOT.SetBatch(True)

inPath = '/uscms/home/chuyuanl/nobackup/VHH/'
outPath = inPath + 'couplings/'
#years = ['2017','2018']
#signals = ['ZHH','WHH','VHH']
years = ['17+18']
signals = ['VHH']

if not os.path.isdir(outPath):
    os.mkdir(outPath)

class ReCoupling:
    def __init__(self):
        self.CmdLen = 10
        self.Debug = False
        self.RootFiles = {}
        self.InHists = {}
        self.OutHists = {}
        self.OutDirs = {}
        self.OutDirsKeys = []
        self.Years = years
        for year in self.Years:
            self.RootFiles[year] = {}
            for signal in signals:
                self.RootFiles[year][signal] = []
        sampleCouplings = [{'CV':0.5},{'CV':1.5},{'C2V':0.0},{'C2V':2.0},{'C3':0.0},{'C3':2.0}]
        sampleFilenames = fh.getCouplingList('CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0')
        cMat = np.empty((6,6))
        for i in range(len(sampleCouplings)):
            cMat[i][:]=self.GetWeights(**sampleCouplings[i])
        self.CInv = np.linalg.pinv(cMat)
        for year in self.Years:
            for filenames in sampleFilenames:
                if 'ZHH' in signals: self.RootFiles[year]['ZHH'].append(ROOT.TFile(inPath + filenames[0] + year + '/hists.root'))
                if 'WHH' in signals: self.RootFiles[year]['WHH'].append(ROOT.TFile(inPath + filenames[1] + year + '/hists.root'))
                if 'VHH' in signals: self.RootFiles[year]['VHH'].append(ROOT.TFile(inPath + filenames[2] + year + '/hists.root'))
        self.InDirs = self.RootFiles[self.Years[0]][signals[0]][0].GetDirectory('')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for year in self.Years:
            for signal in self.RootFiles[year].keys():
                for file in self.RootFiles[year][signal]:
                    if self.Debug: print('Close'.ljust(self.CmdLen) + file.GetName())
                    file.Close()

    # coupling
    def GetWeights(self, CV = 1.0, C2V = 1.0, C3 = 1.0):
        return np.array([CV**2 * C3**2, CV**4, C2V**2, CV**3 * C3, CV * C3 * C2V, CV**2 * C2V])
    
    # string parsing
    def GetDir(self, path):
        return '/'.join(path.split('/')[:-1])

    def SplitPath(self, path):
        return [x for x in path.split('/') if x !='']

    def JoinPath(self, path, file):
        return '/'.join(self.SplitPath(path) + [file])

    def ToStr(self, f):
        return '{:.1f}'.format(f).replace('.', '_')

    def Match(self, pattern, string):
        return re.match('^'+re.escape(pattern).replace('\*', '(.*?)')+'$', string) is not None

    # histogram
    def SumHists(self, hists, weights):
        sum = hists[0].Clone()
        sum.Scale(weights[0])
        for i in range(1,len(hists)):
            sum.Add(hists[i],weights[i])       
        return sum

    def GetInHists(self, year, signal, path):
        hists = []
        for file in self.RootFiles[year][signal]:
            hists.append(file.Get(path))
        return hists

    # TDirectory
    def AddOutDir(self, path):
        dir = self.GetDir(path)
        if dir not in self.OutDirs:
            self.OutDirs[dir] = ''
            self.OutDirsKeys = sorted(self.OutDirs.keys())

    def RemoveOutDir(self, path):
        dir = self.GetDir(path)
        if dir in self.OutDirs:
            for file in self.OutHists:
                if dir in file:
                    return
            del self.OutDirs[dir]
            self.OutDirsKeys = sorted(self.OutDirs.keys())

    def AddHist(self, path):
        if path not in self.OutHists:
            self.OutHists[path] = ''
            self.AddOutDir(path)
            if self.Debug: print('Add'.ljust(self.CmdLen) + path)

    def RemoveHist(self, path):
        if path in self.OutHists:
            del self.OutHists[path]
            self.RemoveOutDir(path)
            if self.Debug: print('Remove'.ljust(self.CmdLen) + path)

    def AddDir(self, path):
        currentDir = self.InDirs.GetDirectory(path)
        if(currentDir):
            for file in currentDir.GetListOfKeys():
                self.AddDir(self.JoinPath(path, file.GetName()))
        else:
            self.AddHist(path)
            
    def RemoveDir(self, path):
        currentDir = self.InDirs.GetDirectory(path)
        if(currentDir):
            for file in currentDir.GetListOfKeys():
                self.RemoveDir(self.JoinPath(path, file.GetName()))
        else:
            self.RemoveHist(path)

    # TDirectory wildcard
    def InitInHistsStep(self, path):
        currentDir = self.InDirs.GetDirectory(path)
        if(currentDir):
            for file in currentDir.GetListOfKeys():
                self.InitInHistsStep(self.JoinPath(path, file.GetName()))
        else:
            self.InHists[path] = ''

    def InitInHists(self):
        if not self.InHists:
            self.InitInHistsStep('')

    def AddHists(self, paths):
        self.InitInHists()
        patterns = [self.SplitPath(path) for path in paths]
        for path in self.InHists.keys():
            dirs = self.SplitPath(path)
            for pattern in patterns:
                if len(dirs)!=len(pattern): continue
                match = True
                for i in range(len(pattern)):
                    if not self.Match(pattern[i], dirs[i]): 
                        match = False
                        break
                if match:
                    self.AddHist(path)

    def RemoveHists(self, paths):
        self.InitInHists()
        patterns = [self.SplitPath(path) for path in paths]
        for path in self.InHists.keys():
            dirs = self.SplitPath(path)
            for pattern in patterns:
                if len(dirs)!=len(pattern): continue
                match = True
                for i in range(len(pattern)):
                    if not self.Match(pattern[i], dirs[i]): 
                        match = False
                        break
                if match:
                    self.RemoveHist(path)

    # create root file
    def BuildDirs(self, file):
        for directory in self.OutDirsKeys:
            file.mkdir(directory)

    def Create(self, CV = 1.0, C2V = 1.0, C3 = 1.0):
        weight = self.GetWeights(CV,C2V,C3)
        weight = np.matmul(weight, self.CInv)
        if self.Debug: print('Weight'.ljust(self.CmdLen) + np.array2string(weight, formatter={'float_kind':lambda x: "%.2f" % x}))
        for year in self.Years:
            for signal in self.RootFiles[year].keys():
                outName = outPath + signal+'To4B_CV_'+self.ToStr(CV)+'_C2V_'+self.ToStr(C2V)+'_C3_'+self.ToStr(C3)+'_'+year+'.root'
                outFile = ROOT.TFile(outName,'recreate')
                self.BuildDirs(outFile)
                for hist in self.OutHists.keys():
                    outHist = self.SumHists(self.GetInHists(year, signal, hist), weight)
                    outFile.cd(self.GetDir(hist))
                    outHist.Write()  
                outFile.Close()
                if self.Debug: print('Create'.ljust(self.CmdLen) + signal + ' CV=' + self.ToStr(CV) + ',C2V=' + self.ToStr(C2V) + ',C3=' + self.ToStr(C3) + ' ' + year)
    
if __name__ == '__main__':
    with ReCoupling() as producer:
        producer.Debug = True
        # producer.AddHists(['passMjjOth/fourTag/mainView/HHSR/*','passMjjOth/fourTag/mainView/HHSR/v4j/*',
        # 'passSvB/fourTag/mainView/HHSR/*','passSvB/fourTag/mainView/HHSR/v4j/*'])
        # producer.RemoveHists(['pass*/fourTag/mainView/HHSR/SvB*','pass*/fourTag/mainView/HHSR/FvT*'])
        # producer.AddHists(['passMjjOth/fourTag/mainView/HHSR/SvB_MA_ps','passSvB/fourTag/mainView/HHSR/SvB_MA_ps'])
        # for value in range(-10,11,1):
        #     producer.Create(C2V=value)
        #     producer.Create(C3=value)


#LO Madgraph xsecs
#WHH_CV_0_5_C2V_1_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   0.0002864 +- 9.158e-07 pb
#WHH_CV_1_5_C2V_1_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   0.0008897 +- 3.418e-06 pb 
#WHH_CV_1_0_C2V_2_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   0.001114 +- 3.251e-06 pb
#WHH_CV_1_0_C2V_0_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   0.0001492 +- 6.739e-07 pb
#WHH_CV_1_0_C2V_1_0_C3_2_0_13TeV-madgraph.log:     Cross-section :   0.0006848 +- 1.987e-06 pb
#WHH_CV_1_0_C2V_1_0_C3_0_0_13TeV-madgraph.log:     Cross-section :   0.0002366 +- 1.025e-06 pb

#WHH_CV_1_0_C2V_1_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   0.0004157 +- 1.319e-06 pb

#ZHH_CV_1_0_C2V_1_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   0.0002632 +- 1.022e-06 pb
#ZHH_CV_1_0_C2V_2_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   0.0006739 +- 2.855e-06 pb
#ZHH_CV_1_0_C2V_1_0_C3_2_0_13TeV-madgraph.log:     Cross-section :   0.0004233 +- 1.411e-06 pb
#ZHH_CV_1_0_C2V_0_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   9.027e-05 +- 3.358e-07 pb
#ZHH_CV_0_5_C2V_1_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   0.0001652 +- 5.321e-07 pb
#ZHH_CV_1_5_C2V_1_0_C3_1_0_13TeV-madgraph.log:     Cross-section :   0.000573 +- 2.833e-06 pb
#ZHH_CV_1_0_C2V_1_0_C3_0_0_13TeV-madgraph.log:     Cross-section :   0.0001539 +- 8.34e-07 pb

