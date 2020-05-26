import time, os, sys
import multiprocessing
from glob import glob
from copy import copy
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, 'ZZ4b/nTupleAnalysis/scripts/') #https://github.com/patrickbryant/PlotTools
import matplotlibHelpers as pltHelper

import argparse
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-d', '--data', default='/uscms/home/bryantp/nobackup/ZZ4b/data2018/picoAOD.h5',    type=str, help='Input dataset file in hdf5 format')
parser.add_argument('--data4b',     default=None, help="Take 4b from this file if given, otherwise use --data for both 3-tag and 4-tag")
parser.add_argument('-t', '--ttbar',      default='',    type=str, help='Input MC ttbar file in hdf5 format')
parser.add_argument('--ttbar4b',          default=None, help="Take 4b ttbar from this file if given, otherwise use --ttbar for both 3-tag and 4-tag")
parser.add_argument('-s', '--signal',     default='', type=str, help='Input dataset file in hdf5 format')
parser.add_argument('-o', '--outdir',     default='', type=str, help='outputDirectory')
parser.add_argument('--weightName', default="mcPseudoTagWeight", help='Which weights to use for JCM.')
parser.add_argument('--FvTName', default="FvT", help='Which weights to use for FvT.')
args = parser.parse_args()

def getFrame(fileName):
    yearIndex = fileName.find('201')
    year = float(fileName[yearIndex:yearIndex+4])
    print("Reading",fileName)
    thisFrame = pd.read_hdf(fileName, key='df')
    thisFrame['year'] = pd.Series(year*np.ones(thisFrame.shape[0], dtype=np.float32), index=thisFrame.index)
    return thisFrame

outputDir = args.outdir
if not os.path.isdir(outputDir):
    print("Making output dir",outputDir)
    os.mkdir(outputDir)

fileReaders = multiprocessing.Pool(10)

weightName = args.weightName
print("Using JCM weight with name: ",weightName)

FvTName = args.FvTName
print("Using FvT weight with name: ",FvTName)


class nameTitle:
    def __init__(self,name,title):
        self.name = name
        self.title= title

class classInfo:
    def __init__(self, abbreviation='', name='', index=None, color=''):
        self.abbreviation = abbreviation
        self.name = name
        self.index = index
        self.color = color

d4 = classInfo(abbreviation='d4', name=  'FourTag Data',       index=0, color='red')
d3 = classInfo(abbreviation='d3', name= 'ThreeTag Data',       index=1, color='orange')
t4 = classInfo(abbreviation='t4', name= r'FourTag $t\bar{t}$', index=2, color='green')
t3 = classInfo(abbreviation='t3', name=r'ThreeTag $t\bar{t}$', index=3, color='cyan')
zz = classInfo(abbreviation='zz', name=r'$ZZ$ MC $\times100$', index=4, color='blue')
zh = classInfo(abbreviation='zh', name=r'$ZH$ MC $\times100$', index=5, color='violet')

dfs = []

# Read .h5 files
dataFiles = glob(args.data)
if args.data4b:
    dataFiles += glob(args.data4b)    

results = fileReaders.map_async(getFrame, sorted(dataFiles))
frames = results.get()
dfD = pd.concat(frames, sort=False)

print("Add true class labels to data")
dfD['d4'] =  dfD.fourTag
dfD['d3'] = (dfD.fourTag+1)%2
dfD['t4'] = pd.Series(np.zeros(dfD.shape[0], dtype=np.uint8), index=dfD.index)
dfD['t3'] = pd.Series(np.zeros(dfD.shape[0], dtype=np.uint8), index=dfD.index)
dfD['zz'] = pd.Series(np.zeros(dfD.shape[0], dtype=np.uint8), index=dfD.index)
dfD['zh'] = pd.Series(np.zeros(dfD.shape[0], dtype=np.uint8), index=dfD.index)

dfs.append(dfD)

# Read .h5 files
ttbarFiles = glob(args.ttbar)
if args.ttbar4b:
    ttbarFiles += glob(args.ttbar4b)    


results = fileReaders.map_async(getFrame, sorted(ttbarFiles))
frames = results.get()
dfT = pd.concat(frames, sort=False)

print("Add true class labels to ttbar MC")
dfT['t4'] =  dfT.fourTag
dfT['t3'] = (dfT.fourTag+1)%2
dfT['d4'] = pd.Series(np.zeros(dfT.shape[0], dtype=np.uint8), index=dfT.index)
dfT['d3'] = pd.Series(np.zeros(dfT.shape[0], dtype=np.uint8), index=dfT.index)
dfT['zz'] = pd.Series(np.zeros(dfT.shape[0], dtype=np.uint8), index=dfT.index)
dfT['zh'] = pd.Series(np.zeros(dfT.shape[0], dtype=np.uint8), index=dfT.index)

dfs.append(dfT)

if args.signal:
    frames = []
    for fileName in sorted(glob(args.signal)):
        yearIndex = fileName.find('201')
        year = float(fileName[yearIndex:yearIndex+4])
        print("Reading",fileName)
        thisFrame = pd.read_hdf(fileName, key='df')
        print("Add year to dataframe",year)#,"encoded as",(year-2016)/2)
        thisFrame['year'] = pd.Series(year*np.ones(thisFrame.shape[0], dtype=np.float32), index=thisFrame.index)
        print("Add true class labels to signal")
        if "ZZ4b201" in fileName: 
            index = zz.index
            thisFrame['zz'] = thisFrame.fourTag
            thisFrame['zh'] = pd.Series(np.zeros(thisFrame.shape[0], dtype=np.uint8), index=thisFrame.index)
        if "ZH4b201" in fileName: 
            index = zh.index
            thisFrame['zz'] = pd.Series(np.zeros(thisFrame.shape[0], dtype=np.uint8), index=thisFrame.index)
            thisFrame['zh'] = thisFrame.fourTag
        thisFrame['t4'] = pd.Series(np.zeros(thisFrame.shape[0], dtype=np.uint8), index=thisFrame.index)
        thisFrame['t3'] = pd.Series(np.zeros(thisFrame.shape[0], dtype=np.uint8), index=thisFrame.index)
        thisFrame['d4'] = pd.Series(np.zeros(thisFrame.shape[0], dtype=np.uint8), index=thisFrame.index)
        thisFrame['d3'] = pd.Series(np.zeros(thisFrame.shape[0], dtype=np.uint8), index=thisFrame.index)
        frames.append(thisFrame)
    dfS = pd.concat(frames, sort=False)
    dfs.append(dfS)


print("concatenate dataframes")
df = pd.concat(dfs, sort=False)



class dataFrameOrganizer:
    def __init__(self, dataFrame):
        self.df = dataFrame
        self.dfSelected = dataFrame
        self.dfd4 = None
        self.dfd3 = None
        self.dft4 = None
        self.dft3 = None
        self.dfbg = None
        self.dfzz = None
        self.dfzh = None
        self.dfsg = None

    def applySelection(self, selection):
        print("Apply selection")
        self.dfSelected = self.df.loc[ selection ]
        
        self.dfd4 = self.dfSelected.loc[ self.dfSelected.d4==True ]
        self.dfd3 = self.dfSelected.loc[ self.dfSelected.d3==True ]
        self.dft4 = self.dfSelected.loc[ self.dfSelected.t4==True ]
        self.dft3 = self.dfSelected.loc[ self.dfSelected.t3==True ]
        self.dfbg = self.dfSelected.loc[ (self.dfSelected.d3==True) | (self.dfSelected.t4==True) ]
        if args.signal:
            self.dfzz = self.dfSelected.loc[ self.dfSelected.zz==True ]
            self.dfzh = self.dfSelected.loc[ self.dfSelected.zh==True ]
            self.dfsg = self.dfSelected.loc[ (self.dfSelected.zz==True) | (self.dfSelected.zh==True) ]

    def plotVar(self, var, bins=None, xmin=None, xmax=None, reweight=False):

        if reweight:
            ttbarWeights = -getattr(self.dft3,weightName) * getattr(self.dft3,FvTName)
            # multijetWeights = np.concatenate((self.dfd3.mcPseudoTagWeight * self.dfd3.FvT, -self.dft3.mcPseudoTagWeight * self.dft3.FvT))
            multijet = self.dfd3[var]
            multijetWeights = getattr(self.dfd3,weightName) * getattr(self.dfd3,FvTName)
            # backgroundWeights = np.concatenate((self.dfd3.mcPseudoTagWeight * self.dfd3.FvT, -self.dft3.mcPseudoTagWeight * self.dft3.FvT, self.dft4.mcPseudoTagWeight))
            background = np.concatenate((self.dfd3[var], self.dft4[var]))
            backgroundWeights = np.concatenate((getattr(self.dfd3,weightName) * getattr(self.dfd3,FvTName), getattr(self.dft4,weightName)))
        else:
            ttbarWeights = -getattr(self.dft3,weightName)
            multijet = np.concatenate((self.dfd3[var], self.dft3[var]))
            multijetWeights = np.concatenate((getattr(self.dfd3,weightName), -getattr(self.dft3,weightName)))
            # multijetWeights = self.dfd3.mcPseudoTagWeight
            # background = np.concatenate((self.dfd3[var], self.dft3[var], self.dft4[var]))
            # backgroundWeights = np.concatenate((self.dfd3.mcPseudoTagWeight, -self.dft3.mcPseudoTagWeight, self.dft4.mcPseudoTagWeight))
            background = np.concatenate((self.dfd3[var], self.dft3[var], self.dft4[var]))
            backgroundWeights = np.concatenate((getattr(self.dfd3,weightName), -getattr(self.dft3,weightName), getattr(self.dft4,weightName)))
            # backgroundWeights = np.concatenate((self.dfd3.mcPseudoTagWeight, self.dft4.mcPseudoTagWeight))

        self.dsd4 = pltHelper.dataSet(name=d4.name, 
                                      points =self.dfd4[var],
                                      weights=getattr(self.dfd4,weightName), 
                                      color=d4.color, alpha=1.0, linewidth=1)
        self.bkgd = pltHelper.dataSet(name='Background Model', 
                                      points =background,
                                      weights=backgroundWeights, 
                                      color='brown', alpha=1.0, linewidth=1)
        self.dst4 = pltHelper.dataSet(name=t4.name, 
                                      points =self.dft4[var],
                                      weights=getattr(self.dft4,weightName), 
                                      color=t4.color, alpha=1.0, linewidth=1)
        self.dsm3 = pltHelper.dataSet(name='ThreeTag Multijet', 
                                      points =multijet,
                                      weights=multijetWeights,
                                      color=d3.color, alpha=1.0, linewidth=1)
        self.dst3 = pltHelper.dataSet(name=t3.name, 
                                      points=self.dft3[var],
                                      weights=ttbarWeights,
                                      color=t3.color, alpha=1.0, linewidth=1)
        datasets = [self.dsd4,self.bkgd,self.dst4,self.dsm3,self.dst3]
        if self.dfzz is not None:
            self.dszz = pltHelper.dataSet(name=zz.name,
                                          points=self.dfzz[var],
                                          weights=getattr(self.dfzz,weightName)*100,
                                          color=zz.color, alpha=1.0, linewidth=1)
            datasets += [self.dszz]
        if self.dfzh is not None:
            self.dszh = pltHelper.dataSet(name=zh.name,
                                          points=self.dfzh[var],
                                          weights=getattr(self.dfzh,weightName)*100,
                                          color=zh.color, alpha=1.0, linewidth=1)
            datasets += [self.dszh]

        if type(bins)!=list:
            if not bins: bins=50
            if type(xmin)==type(None): xmin = self.dfSelected[var].min()
            if type(xmax)==type(None): xmax = self.dfSelected[var].max()
            width = (xmax-xmin)/bins
            bins = [xmin + b*width for b in range(0,bins+1)]

        args = {'dataSets': datasets,
                'ratio': [0,1],
                'ratioRange': [0.9,1.1] if reweight else [0.5, 1.5],
                'ratioTitle': 'Data / Model',
                'bins': bins,
                'xmin': xmin,
                'xmax': xmax,
                'xlabel': var.replace('_',' '),
                'ylabel': 'Events / Bin',
                }
        fig = pltHelper.histPlotter(**args)
        figName = outputDir + "/"+var+('_reweight' if reweight else '')+'.pdf'
        fig.savefig(figName)
        print(figName)

    def hist2d(self, dfName, xvar, yvar ,bins=50,range=None,reweight=False): # range = [[xmin, xmax], [ymin, ymax]]
        df = getattr(self,dfName)
        x,y = df[xvar],df[yvar]
        if reweight:
            weights = getattr(df,weightName) * (getattr(df,FvTName) * (1-df.fourTag) + df.fourTag)
        else:
            weights = getattr(df,weightName)
        xlabel = xvar.replace('_',' ')
        ylabel = yvar.replace('_',' ')
        args = {'x':x, 'y':y, 'weights':weights,
                'xlabel': xlabel,
                'ylabel': ylabel,
                'zlabel': 'Events / Bin',
                'bins': bins,
                'range': range,
                }
        fig = pltHelper.hist2d(**args)
        figName = outputDir +"/"+dfName+"_"+xvar+"_vs_"+yvar+("_reweight" if reweight else "")+".pdf"
        fig.savefig(figName)
        print(figName)


print("Blind 4 tag SR")
df = df.loc[ (df.SR==False) | (df.d4==False) ]

dfo = dataFrameOrganizer(df)

dfo.applySelection( (dfo.df.passHLT==True) & (dfo.df.SB==True) & (dfo.df.xWt > 2) )

#
# Example plots
#

# dfo.plotVar('dRjjOther')
# dfo.plotVar('dRjjOther', reweight=True)
# dfo.hist2d('dfbg', 'canJet0_eta', 'FvT')

# #dfo.df['SvB_q_max'] = dfo.df[['SvB_q_1234', 'SvB_q_1324', 'SvB_q_1423']].idxmax(axis=1)
# SvB_q_score = dfo.df[['SvB_q_1234', 'SvB_q_1324', 'SvB_q_1423']].values
# FvT_q_score = dfo.df[['FvT_q_1234', 'FvT_q_1324', 'FvT_q_1423']].values
# SvB_q_max = np.amax(SvB_q_score, axis=1, keepdims=True)
# FvT_q_max = np.amax(FvT_q_score, axis=1, keepdims=True)
# events, SvB_q_max_index = np.where(SvB_q_score==SvB_q_max)
# events, FvT_q_max_index = np.where(FvT_q_score==FvT_q_max)
# dfo.df['SvB_q_max_index'] = SvB_q_max_index
# dfo.df['FvT_q_max_index'] = FvT_q_max_index
# FvT_q_at_SvB_q_max_index = FvT_q_score[events, SvB_q_max_index]
# SvB_q_at_FvT_q_max_index = SvB_q_score[events, FvT_q_max_index]
# dfo.df['FvT_q_at_SvB_q_max_index'] = FvT_q_at_SvB_q_max_index
# dfo.df['SvB_q_at_FvT_q_max_index'] = SvB_q_at_FvT_q_max_index

# dfo.applySelection( (dfo.df.passHLT==True) & (dfo.df.SB==True) & (dfo.df.xWt > 2) )

# def plot_q_scores():
#     names = ['SvB_q_1234', 'SvB_q_1324', 'SvB_q_1423', 'FvT_q_1234', 'FvT_q_1324', 'FvT_q_1423']
#     for name in names:
#         dfo.plotVar(name, xmin=0, xmax=1, bins=20, reweight=True)
#     dfo.plotVar('SvB_q_max_index', xmin=-0.5, xmax=2.5, bins=3, reweight=True)
#     dfo.plotVar('FvT_q_max_index', xmin=-0.5, xmax=2.5, bins=3, reweight=True)
#     dfo.plotVar('FvT_q_at_SvB_q_max_index', xmin=0, xmax=1, bins=20, reweight=True)    
#     dfo.plotVar('SvB_q_at_FvT_q_max_index', xmin=0, xmax=1, bins=20, reweight=True)    

# plot_q_scores()
