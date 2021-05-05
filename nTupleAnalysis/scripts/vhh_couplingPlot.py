#distribution in one plot
#svb/m/svb&m/no
import os
import math
from array import array
import ROOT
import sys
import numpy as np
import vhh_fileHelper as fh

ROOT.gStyle.SetPalette(112)
ROOT.gROOT.SetBatch(True) 
ROOT.gStyle.SetOptStat(ROOT.kFALSE)

mcOnly=False
cpscan = 'c3'
#cpscan='c2v'
error = False
inputPath = '/home/chuyuan/data/VHH/data/couplings/'
cutLabels = {'passMDRs':'#font[42]{#Delta R{j,j}}','passNjOth':'#font[42]{N_{j}#geq 6}','passMjjOth':'#font[42]{60#leq m_{V}#leq 110}',
'passSvB':'#font[42]{60#leq m_{V}#leq 110, SvB> 0.8}','SvBOnly':'#font[42]{SvB> 0.8}',
'fourTag':'4b', 'threeTag':'3b'}
years=['17+18']
cuts=['passMjjOth','passSvB']
regions=['HHSR']
tags=['fourTag']
hists=['mjjOther','ptjjOther','v4j/m_l','v4j/phi','v4j/pt_m','v4j/pt_l','v4j/eta','s4j','SvB_MA_ps']
files={}


def GetDir(path):
    return '/'.join(path.split('/')[:-1])

def MakePalette(min,max,step,title):
    n = int((max-min)/step+1)
    p=ROOT.TH2F("","",n,min-step/2.0,max+step/2.0,1,0,1)
    c=[]
    p.SetMaximum(255)
    p.SetMinimum(0)
    for i in np.arange(min,max+step,step):
        pos = int((254/n)*((i-min)/step+1))
        c.append(ROOT.TColor.GetColorPalette(pos))
        p.Fill(i,0.5,pos)
    p.GetXaxis().SetLabelSize(0.15)
    p.GetXaxis().SetTitleSize(0.15)
    p.GetXaxis().SetTitle(title)
    p.GetXaxis().SetNdivisions(n)
    p.GetYaxis().SetLabelSize(0)
    p.GetYaxis().SetTickLength(0)
    return p,c


def Main(mcOnly,cpscan,errorbar,selected=''):
    outputPath = '/home/chuyuan/data/VHH/data/couplingPlot_'+cpscan+('_e' if errorbar else '')+('_MC' if mcOnly else '')+selected+'/'

    def PlotAll(couplings, palette, colors):
        for year in years:
            files={}
            for coupling in couplings:
                files[coupling]=ROOT.TFile(inputPath+coupling+year+'.root')
            for histname in hists:
                for cut in cuts:
                    for tag in tags:
                        for region in regions:
                            histpath = '/'.join([cut,tag,'mainView',region,histname])
                            path =outputPath+histpath
                            if(not os.path.isdir(GetDir(path))):
                                os.makedirs(GetDir(path))
                            c1 = ROOT.TCanvas()
                            pad1=ROOT.TPad('','',0.0,0.2,1.0,1.0)
                            pad1.Draw()
                            pad2=ROOT.TPad('','',0.0,0.0,1.0,0.2)
                            pad2.SetBottomMargin(0.5)
                            pad2.Draw()
                            pad1.cd()
                            loop =range(len(couplings))
                            if mcOnly or selected=='_large':
                                loop=loop[::-1]
                            for i in loop:
                                hist=files[couplings[i]].Get(histpath)
                                hist.SetLineColor(colors[i])
                                hist.Draw('same hist pc'+(' E' if errorbar else ''))
                            pad2.cd()
                            palette.Draw('col')
                            c1.Print(path+'.pdf')
            for coupling in couplings:
                files[coupling].Close()
    cp=[]
    label=''
    max = 10
    min = -10
    if mcOnly:
        max =2
        min =0
    if selected == '_large':
        max = 10
        min = 5
    elif selected == '_small':
        max = -1
        min = -10
    for i in range(min,max+1):
        if cpscan=='c3':
            cp.append(fh.getCoupling(C3=fh.F2Str(i))[2])
            label='#kappa_{#lambda}'
        elif cpscan=='c2v':
            cp.append(fh.getCoupling(C2V=fh.F2Str(i))[2])
            label='C_{2V}'
    p,c=MakePalette(min,max,1,'#font[42]{'+label+'}')
    PlotAll(cp, p, c)

for mc in [True,False]:
    for cp in ['c3','c2v']:
        for e in [True,False]:
            if not e or not mc:
                Main(mc,cp,e)
for cp in ['c3']:
    for selected in ['_large','_small']:
            Main(False,cp,False,selected)