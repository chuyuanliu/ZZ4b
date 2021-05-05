import os
import math
from array import array
import ROOT
import sys
sys.path.insert(0, '.')
import Helper.ROOTCanvas as pltC
import Helper.LaTeX as tex
import vhh_fileHelper as fh

couplings = ',CV:0_5,CV:1_5,C2V:0_0,C2V:2_0,C3:0_0,C3:2_0'
couplings = fh.getCouplingList(couplings)
inputDir = '/uscms/home/chuyuanl/nobackup/VHH/'
outputDir = inputDir + 'SvBPlots/'
if not os.path.isdir(outputDir):
    os.mkdir(outputDir)

def setRange(range, value):
    if value<range[0]: range[0]=value
    if value>range[1]: range[1]=value

def plotSvB(sel, hist, cuts):
    for _year in ['17+18']:
        background = {}
        signal = {}
        signal_n = {}
        ttbar = {}
        SvB = {}
        sensitivity = {}

        sigRange=[0,0]
        bkgRange=[0,0]
        svbRange=[1,0]
        senRange=[1,0]
        sigNRange=[1,0]
        legendFont=0.02
        legendW=0.45
        legendH=0.15
        for coupling in couplings:
            cp = coupling[3]
            fTTBar=ROOT.TFile(inputDir + "TT" + _year + "/hists_j_r.root")
            fBkg=ROOT.TFile(inputDir + "data" + _year + "/hists_j_r.root")
            fSig=ROOT.TFile(inputDir + coupling[2] + _year + "/hists.root")
            
            TTSR=fTTBar.Get(sel.Text+"/fourTag/mainView/HHSR/" + hist.Text)
            TTCR=fTTBar.Get(sel.Text+"/fourTag/mainView/CR/" + hist.Text)
            N3b=fBkg.Get(sel.Text+"/threeTag/mainView/HHSR/" + hist.Text).Integral(1,100)
            Bkg=fBkg.Get(sel.Text+"/fourTag/mainView/CR/" + hist.Text)
            Sig=fSig.Get(sel.Text+"/fourTag/mainView/HHSR/" + hist.Text)
            N4b=Bkg.Integral(1,100)-TTCR.Integral(1,100)
            background[cp],signal[cp],ttbar[cp],signal_n[cp]=array( 'd' ), array( 'd' ), array( 'd' ),array( 'd' )
            SvB[cp]=array( 'd' )
            sensitivity[cp]=array('d')
            for cutRange in cuts[1]:
                signal[cp].append(Sig.Integral(cutRange[0], cutRange[1]))
                ttbar[cp].append(TTSR.Integral(cutRange[0], cutRange[1]))
                background[cp].append(N3b/N4b*(Bkg.Integral(cutRange[0], cutRange[1])-TTCR.Integral(cutRange[0], cutRange[1]))+ttbar[cp][-1])
                SvB[cp].append(signal[cp][-1]/background[cp][-1])
                sensitivity[cp].append(signal[cp][-1]/math.sqrt(background[cp][-1]))
                setRange(sigRange,signal[cp][-1])
                setRange(bkgRange,background[cp][-1])
                setRange(svbRange,SvB[cp][-1])
                setRange(senRange,sensitivity[cp][-1])
            for i in range(len(signal[cp])):
                signal_n[cp].append(signal[cp][i]/signal[cp][0])
                setRange(sigNRange,signal_n[cp][-1])
            fSig.Close()
            fBkg.Close()
            fTTBar.Close()

        sigRange[0]=sigRange[0]*0.9
        sigRange[1]=sigRange[1]*1.1
        svbRange[0]=svbRange[0]*0.8
        svbRange[1]=svbRange[1]*1
        senRange[0]=senRange[0]*0.9
        senRange[1]=senRange[1]*1.1

        cHelper = pltC.ROOTCanvas()
        cHelper.XLabel.Text = hist.TeX
        cHelper.YLabel.Text = '#font[42]{S/B}'
        cHelper.TopRight.Text = sel.TeX
        cHelper.TopMid.Text = '#font[42]{'+_year+' ZHH and WHH}'
        cHelper.Var.YAxisType = 'log'
        cHelper.Var.YMax = svbRange[1]
        cHelper.Var.YMin = svbRange[0]
        cHelper.Var.XMax = cuts[0][-1]
        cHelper.Var.XMin = cuts[0][0]

        c1 = cHelper.GetCanvas('S/B log')
        legend=ROOT.TLegend(legendW,legendH)
        legend.SetTextSize(legendFont)
        legend.SetBorderSize(0)
        legend.SetNColumns(2)
        MultiGraph=ROOT.TMultiGraph()
        _color=0
        for coupling in couplings:
            cp = coupling[3]
            Graph=ROOT.TGraph(len(cuts[0]),cuts[0],SvB[cp])
            Graph.SetLineColor(pltC.ColorGradient[_color])
            Graph.SetLineWidth(1)
            _color+=1
            legend.AddEntry(Graph,cp)
            MultiGraph.Add(Graph)
        MultiGraph.Draw("LP")
        legend.Draw()
        c1.Print(outputPath+_year+"_SvB_log.pdf")

        cHelper.Var.YAxisType = 'linear'
        cHelper.Var.YMax = sigRange[1]
        cHelper.Var.YMin = sigRange[0]
        cHelper.YLabel.Text = '#font[42]{Signal Yield}'
        c1 = cHelper.GetCanvas('signal')
        legend=ROOT.TLegend(legendW,legendH)
        legend.SetTextSize(legendFont)
        legend.SetBorderSize(0)
        legend.SetNColumns(2)
        MultiGraph=ROOT.TMultiGraph()
        _color=0
        for coupling in couplings:
            cp = coupling[3]
            Graph=ROOT.TGraph(len(cuts[0]),cuts[0],signal[cp])
            Graph.SetLineColor(pltC.ColorGradient[_color])
            Graph.SetLineWidth(1)
            _color+=1
            legend.AddEntry(Graph,cp)
            MultiGraph.Add(Graph)         
        MultiGraph.Draw("LP")
        legend.Draw()
        c1.Print(outputPath+_year+"_signal.pdf")

        cHelper.Var.YMax = sigNRange[1]
        cHelper.Var.YMin = sigNRange[0]
        cHelper.YLabel.Text = '#font[42]{Signal Acceptance}'
        c1 = cHelper.GetCanvas('signal acceptance')
        legend=ROOT.TLegend(legendW,legendH)
        legend.SetTextSize(legendFont)
        legend.SetBorderSize(0)
        legend.SetNColumns(2)
        MultiGraph=ROOT.TMultiGraph()
        _color=0
        for coupling in couplings:
            cp = coupling[3]
            Graph=ROOT.TGraph(len(cuts[0]),cuts[0],signal_n[cp])
            Graph.SetLineColor(pltC.ColorGradient[_color])
            Graph.SetLineWidth(1)
            _color+=1
            legend.AddEntry(Graph,cp)
            MultiGraph.Add(Graph)         
        MultiGraph.Draw("LP")
        legend.Draw()
        c1.Print(outputPath+_year+"_signal_acceptance.pdf")


        cHelper.Var.YMax = bkgRange[1]
        cHelper.Var.YMin = bkgRange[0]
        cHelper.YLabel.Text = '#font[42]{Background Yield}'
        c1 = cHelper.GetCanvas('background')
        _color=0
        coupling = couplings[0]
        cp = coupling[3]
        Graph=ROOT.TGraph(len(cuts[0]),cuts[0],background[cp])
        Graph.SetLineColor(pltC.ColorGradient[_color])
        Graph.SetLineWidth(1)
        Graph.Draw("LP")
        c1.Print(outputPath+_year+"_background.pdf")

        cHelper.Var.YMax = senRange[1]
        cHelper.Var.YMin = senRange[0]
        cHelper.YLabel.Text = '#font[42]{Sensitivity S/#sqrt{B}}'
        cHelper.Var.YAxisType = 'log'
        c1 = cHelper.GetCanvas('sensitivity log')
        legend=ROOT.TLegend(legendW,legendH)
        legend.SetTextSize(legendFont)
        legend.SetBorderSize(0)
        legend.SetNColumns(2)
        MultiGraph=ROOT.TMultiGraph()
        _color=0
        for coupling in couplings:
            cp = coupling[3]
            Graph=ROOT.TGraph(len(cuts[0]),cuts[0],sensitivity[cp])
            Graph.SetLineColor(pltC.ColorGradient[_color])
            Graph.SetLineWidth(1)
            _color+=1
            legend.AddEntry(Graph,cp)
            MultiGraph.Add(Graph)
        MultiGraph.Draw("LP")
        legend.Draw()
        c1.Print(outputPath+_year+"_sensitivity_log.pdf")

outputPath = outputDir+'SvBClassifier/'
if not os.path.isdir(outputPath):
    os.mkdir(outputPath)
sel = tex.TeXText("passNjOth", "#font[42]{SR, N_{j}#geq 6}")
hist = tex.TeXText("SvB_MA_ps", "#font[42]{cut on SvB Classifier Regressed P(VHH)}")
cuts = [array( 'd' ),[]]
for i in range(0,100,10):
    cuts[0].append(i/100.0)
    cuts[1].append([i+1,100])
plotSvB(sel, hist, cuts)

outputPath = outputDir+'MassWindow/'
if not os.path.isdir(outputPath):
    os.mkdir(outputPath)
# mjjOther 100 bins 0-500GeV
# 80-85:17,85-90:18, 90-95:19
sel = tex.TeXText("passNjOth", "#font[42]{SR, N_{j}#geq 6}")
hist = tex.TeXText("mjjOther", "#font[42]{m_{V} window width}")
cuts = [array( 'd' ),[]]
center = 18
for delta in range(1,15):
    cuts[0].append(delta*10)
    cuts[1].append([center - delta,center + delta -1])
plotSvB(sel, hist, cuts)