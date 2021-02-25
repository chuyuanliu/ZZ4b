import ROOT
import os
import math
from array import array

import sys
sys.path.insert(1, 'RootHelper')
import plotCanvas as pltC
import vhh_fileHelper as fh

couplings = 'CV:0_5,C2V:0_0,,C3:2_0,C2V:2_0,CV:1_5'
couplings = fh.getCouplingList(couplings)
inputDir = '/uscms/home/chuyuanl/nobackup/VHH/'
outputDir = inputDir + 'SvBPlots/'
if not os.path.isdir(outputDir):
    os.mkdir(outputDir)
#mjjOther 100 bins 0-500GeV
#80-85:17,85-90:18, 90-95:19
center = 18
def plotSvB():
    for _year in ['17+18']:
        background = {}
        signal = {}
        ttbar = {}
        SvB = {}
        sensitivity = {}
        for coupling in couplings:
            cp = coupling[3]
            fTTBar=ROOT.TFile(inputDir + "TT" + _year + "/hists_j_r.root")
            fBkg=ROOT.TFile(inputDir + "data" + _year + "/hists_j_r.root")
            fSig=ROOT.TFile(inputDir + coupling[2] + _year + "/hists.root")

            mVTTSR=fTTBar.Get("passNjOth/fourTag/mainView/HHSR/mjjOther")
            mVTTCR=fTTBar.Get("passNjOth/fourTag/mainView/CR/mjjOther")
            N3b=fBkg.Get("passNjOth/threeTag/mainView/HHSR/mjjOther").Integral(1,100)
            mVBkg=fBkg.Get("passNjOth/fourTag/mainView/CR/mjjOther")
            mVSig=fSig.Get("passNjOth/fourTag/mainView/HHSR/mjjOther")
            N4b=mVBkg.Integral(1,100)-mVTTCR.Integral(1,100)

            background[cp],signal[cp],ttbar[cp],mV=array( 'd' ), array( 'd' ), array( 'd' ), array( 'd' )
            SvB[cp]=array( 'd' )
            sensitivity[cp]=array('d')
            max = 0
            window = [0,0]
            for delta in range(1,15):
                mV.append(delta*10)
                lower = center - delta
                upper = center + delta -1
                signal[cp].append(mVSig.Integral(lower, upper))
                ttbar[cp].append(mVTTSR.Integral(lower, upper))
                background[cp].append(N3b/N4b*(mVBkg.Integral(lower, upper)-mVTTCR.Integral(lower, upper))+ttbar[cp][-1])
                SvB[cp].append(signal[cp][-1]/background[cp][-1])
                sensitivity[cp].append(signal[cp][-1]/math.sqrt(background[cp][-1]))
                if SvB[cp][-1]>max:
                    max=SvB[cp][-1]
                    window=[(lower-1) *5, upper*5]

            #SvB
            # c1=pltC.SetCanvas(cp,pltC.CanvasVariables(_xMax=160,_yMax=4e-4,_yMin=1e-5,_xMin=0,_axisType='log'),
            # pltC.CanvasScales(_xLabelX=0.1,_topLabelY=1.02,_topRightLabelX=0.1,_topMidLabelX=0.35),pltC.CanvasFonts(),
            # _xLabel="#font[42]{m_{V} width}",_yLabel="#font[42]{S/B}",_topRightLabel="#font[42]{N_{jet}#geq 6}")
            # Graph=ROOT.TGraph(len(mV),mV,SvB[cp])
            # print(str(_year)+" "+cp+" "+str(window)+" "+str(max))
            # Graph.Draw("LP")
            # c1.Print(outputDir + str(_year)+"_SvB_"+cp+".pdf")

            fSig.Close()
            fBkg.Close()
            fTTBar.Close()
    
        c1=pltC.SetCanvas(cp,pltC.CanvasVariables(_xMax=160,_yMax=4.2e-4,_yMin=1.6e-5,_xMin=0,_axisType='log'),
        pltC.CanvasScales(_xLabelX=0.1,_topLabelY=1.02,_topRightLabelX=0.1,_topMidLabelX=0.35),pltC.CanvasFonts(),
        _xLabel="#font[42]{m_{V} width}",_yLabel="#font[42]{S/B}",_topRightLabel="#font[42]{N_{jet}#geq 6}",_topMidLabel='#font[42]{2017+2018 ZHH and WHH}')
        legend=ROOT.TLegend(0.53,0.7,0.89,0.89)
        legend.SetTextSize(0.035)
        legend.SetBorderSize(0)
        legend.SetNColumns(1)
        MultiGraph=ROOT.TMultiGraph()
        _color=0
        for coupling in couplings:
            cp = coupling[3]
            Graph=ROOT.TGraph(len(mV),mV,SvB[cp])
            Graph.SetLineColor(pltC.ColorGradient[_color])
            Graph.SetLineWidth(1)
            _color+=1
            legend.AddEntry(Graph,cp)
            MultiGraph.Add(Graph)
        MultiGraph.Draw("LP")
        legend.Draw()
        c1.Print(outputDir+str(_year)+"_SvB_all_log.pdf")

        c1=pltC.SetCanvas(cp,pltC.CanvasVariables(_xMax=160,_yMax=4.0e-4,_yMin=1.5e-5,_xMin=0,_axisType='linear'),
        pltC.CanvasScales(_xLabelX=0.1,_topLabelY=1.02,_topLeftLabelX=0.08,_topRightLabelX=0.1,_topMidLabelX=0.35),pltC.CanvasFonts(),
        _xLabel="#font[42]{m_{V} width}",_yLabel="#font[42]{S/B}",_topRightLabel="#font[42]{N_{jet}#geq 6}",_topMidLabel='#font[42]{2017+2018 ZHH and WHH}')
        legend=ROOT.TLegend(0.53,0.7,0.89,0.89)
        legend.SetTextSize(0.035)
        legend.SetBorderSize(0)
        legend.SetNColumns(1)
        MultiGraph=ROOT.TMultiGraph()
        _color=0
        for coupling in couplings:
            cp = coupling[3]
            Graph=ROOT.TGraph(len(mV),mV,SvB[cp])
            Graph.SetLineColor(pltC.ColorGradient[_color])
            Graph.SetLineWidth(1)
            _color+=1
            legend.AddEntry(Graph,cp)
            MultiGraph.Add(Graph)
        MultiGraph.Draw("LP")
        legend.Draw()
        c1.Print(outputDir+str(_year)+"_SvB_all_linear.pdf")

        c1=pltC.SetCanvas(cp,pltC.CanvasVariables(_xMax=160,_yMax=0.3,_yMin=0,_xMin=0,_axisType='linear'),
        pltC.CanvasScales(_xLabelX=0.1,_topLabelY=1.02,_topRightLabelX=0.1,_topMidLabelX=0.35),pltC.CanvasFonts(),
        _xLabel="#font[42]{m_{V} width}",_yLabel="#font[42]{Signal}",_topRightLabel="#font[42]{N_{jet}#geq 6}",_topMidLabel='#font[42]{2017+2018 ZHH and WHH}')
        legend=ROOT.TLegend(0.13,0.7,0.49,0.89)
        legend.SetTextSize(0.035)
        legend.SetBorderSize(0)
        legend.SetNColumns(1)
        MultiGraph=ROOT.TMultiGraph()
        _color=0
        for coupling in couplings:
            cp = coupling[3]
            Graph=ROOT.TGraph(len(mV),mV,signal[cp])
            Graph.SetLineColor(pltC.ColorGradient[_color])
            Graph.SetLineWidth(1)
            _color+=1
            legend.AddEntry(Graph,cp)
            MultiGraph.Add(Graph)
        MultiGraph.Draw("LP")
        legend.Draw()
        c1.Print(outputDir+str(_year)+"_signal_all.pdf")

        c1=pltC.SetCanvas(cp,pltC.CanvasVariables(_xMax=160,_yMax=2000,_yMin=0,_xMin=0,_axisType='linear'),
        pltC.CanvasScales(_xLabelX=0.1,_topLabelY=1.02,_topRightLabelX=0.1,_topMidLabelX=0.35),pltC.CanvasFonts(),
        _xLabel="#font[42]{m_{V} width}",_yLabel="#font[42]{Background}",_topRightLabel="#font[42]{N_{jet}#geq 6}",_topMidLabel='#font[42]{2017+2018 ZHH and WHH}')
        _color=0
        coupling = couplings[0]
        cp = coupling[3]
        Graph=ROOT.TGraph(len(mV),mV,background[cp])
        Graph.SetLineColor(pltC.ColorGradient[_color])
        Graph.SetLineWidth(1)
        Graph.Draw("LP")
        c1.Print(outputDir+str(_year)+"_background_all.pdf")

        c1=pltC.SetCanvas(cp,pltC.CanvasVariables(_xMax=160,_yMax=6.6e-3,_yMin=5e-4,_xMin=0,_axisType='linear'),
        pltC.CanvasScales(_xLabelX=0.1,_topLabelY=1.02,_topRightLabelX=0.1,_topMidLabelX=0.35),pltC.CanvasFonts(),
        _xLabel="#font[42]{m_{V} width}",_yLabel="#font[42]{Sensitivity S/#sqrt{B}}",_topRightLabel="#font[42]{N_{jet}#geq 6}",_topMidLabel='#font[42]{2017+2018 ZHH and WHH}')
        legend=ROOT.TLegend(0.51,0.43,0.89,0.60)
        legend.SetTextSize(0.035)
        legend.SetBorderSize(0)
        legend.SetNColumns(1)
        MultiGraph=ROOT.TMultiGraph()
        _color=0
        for coupling in couplings:
            cp = coupling[3]
            Graph=ROOT.TGraph(len(mV),mV,sensitivity[cp])
            Graph.SetLineColor(pltC.ColorGradient[_color])
            Graph.SetLineWidth(1)
            _color+=1
            legend.AddEntry(Graph,cp)
            MultiGraph.Add(Graph)
        MultiGraph.Draw("LP")
        legend.Draw()
        c1.Print(outputDir+str(_year)+"_sensitivity_all_linear.pdf")
        c1=pltC.SetCanvas(cp,pltC.CanvasVariables(_xMax=160,_yMax=1e-2,_yMin=6e-4,_xMin=0,_axisType='log'),
        pltC.CanvasScales(_xLabelX=0.1,_topLabelY=1.02,_topRightLabelX=0.1,_topMidLabelX=0.35),pltC.CanvasFonts(),
        _xLabel="#font[42]{m_{V} width}",_yLabel="#font[42]{Sensitivity S/#sqrt{B}}",_topRightLabel="#font[42]{N_{jet}#geq 6}",_topMidLabel='#font[42]{2017+2018 ZHH and WHH}')
        legend=ROOT.TLegend(0.13,0.78,0.89,0.89)
        legend.SetTextSize(0.03)
        legend.SetBorderSize(0)
        legend.SetNColumns(2)
        MultiGraph=ROOT.TMultiGraph()
        _color=0
        for coupling in couplings:
            cp = coupling[3]
            Graph=ROOT.TGraph(len(mV),mV,sensitivity[cp])
            Graph.SetLineColor(pltC.ColorGradient[_color])
            Graph.SetLineWidth(1)
            _color+=1
            legend.AddEntry(Graph,cp)
            MultiGraph.Add(Graph)
        MultiGraph.Draw("LP")
        legend.Draw()
        c1.Print(outputDir+str(_year)+"_sensitivity_all_log.pdf")
plotSvB()