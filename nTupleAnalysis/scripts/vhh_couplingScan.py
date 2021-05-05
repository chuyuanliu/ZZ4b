#distribution in one plot
#svb/m/svb&m/no
import os
import math
from array import array
import ROOT
import sys
sys.path.insert(0, '.')
import Helper.ROOTCanvas as pltC
import vhh_fileHelper as fh

inputPath = '/uscms/home/chuyuanl/nobackup/VHH/couplings/'
histogram = 'mainView/HHSR/v4j/pt_l'
cutLabels = {'passNjOth':'#font[42]{SR, N_{j}#geq 6}','passMjjOth':'#font[42]{SR, 60#leq m_{V}#leq 110}',
'passSvB':'#font[42]{SR, 60#leq m_{V}#leq 110, SvB> 0.8}','SvBOnly':'#font[42]{SR, SvB> 0.8}',
'fourTag':'4b', 'threeTag':'3b'}

signals = ['ZHH','WHH','VHH']
signal = 2
year = '17+18'
minCP = -30
maxCP = 100
step = 10
minAxis = (minCP-step/2.0)/10.0
maxAxis = (maxCP+step/2.0)/10.0
bins = (maxCP-minCP)/step+1

h2s={'fourTag':{}, 'threeTag':{}}
def YieldScan(cut = 'passNjOth', tag = 'fourTag', max=-1):
    cHelper = pltC.ROOTCanvas()
    cHelper.XLabel.Text = '#font[42]{C_{3}}'
    cHelper.YLabel.Text = '#font[42]{C_{2V}}'
    cHelper.TopRight.Text = cutLabels[cut]
    cHelper.TopMid.Text = '#font[42]{'+year+signals[signal]+' Signal '+cutLabels[tag]+'}'
    cHelper.Var.YMax = maxAxis
    cHelper.Var.YMin = minAxis
    cHelper.Var.XMax = maxAxis
    cHelper.Var.XMin = minAxis
    c1 = cHelper.GetCanvas('signal_' + cut + '_' + tag)
    h2s[tag][cut] = ROOT.TH2F('signal_' + cut + '_' + tag, 'signal_' + cut + '_' + tag, bins, minAxis, maxAxis, bins, minAxis,maxAxis)
    for c2v in range(minCP,maxCP+step,step):
        for c3 in range(minCP,maxCP+step,step):
            filename = fh.getCoupling(C2V=fh.F2Str(c2v/10.0), C3=fh.F2Str(c3/10.0))[signal]
            file = ROOT.TFile(inputPath+filename+year+'.root')
            hist = file.Get(cut+'/'+tag+'/'+histogram)
            total = hist.Integral(0,100)
            if (total<0):
                print(str(c2v)+' '+str(c3)+' '+str(total))
            file.Close()
            h2s[tag][cut].Fill(c3/10.0,c2v/10.0,total)
    if max >0:
        h2s[tag][cut].SetMaximum(max)
    # h2s[tag][cut].SetMinimum(0)
    h2s[tag][cut].Draw('same colz')
    c1.Print(inputPath+year+signals[signal]+'_signal_coupling_'+cut+'_'+tag+'_'+fh.F2Str(max)+'.pdf')
    

def RatioScan(cut1 = 'passNjOth', cut2 = 'passNjOth', tag1 = 'fourTag',  tag2 = 'fourTag', max = 1, min = 0, auto = False):
    assert cut1 == cut2 or tag1 == tag2
    cHelper = pltC.ROOTCanvas()
    cHelper.XLabel.Text = '#font[42]{C_{3}}'
    cHelper.YLabel.Text = '#font[42]{C_{2V}}'
    if tag1 == tag2:
        ratio = cut1+'_'+cut2
        ratioLabel = '('+cutLabels[cut1]+')/('+cutLabels[cut2]+')'
        cut = tag1
        cutLabel = cutLabels[tag1]
    elif cut1 == cut2:
        ratio = tag1+'_'+tag2
        ratioLabel = '('+cutLabels[tag1]+')/('+cutLabels[tag2]+')'
        cut = cut1
        cutLabel = cutLabels[cut1]
    cHelper.TopMid.Text = '#font[42]{'+year+signals[signal]+' '+ratioLabel+'}'
    cHelper.TopRight.Text = '#font[42]{'+cutLabel+'}'
    cHelper.Var.YMax = maxAxis
    cHelper.Var.YMin = minAxis
    cHelper.Var.XMax = maxAxis
    cHelper.Var.XMin = minAxis
    c1 = cHelper.GetCanvas('ratio_' + ratio + '_' + cut)
    numerator = h2s[tag1][cut1].Clone()
    denominator = h2s[tag2][cut2]
    numerator.Divide(denominator)
    if auto:
        numerator.SetMaximum(numerator.GetBinContent(numerator.GetMaximumBin()))
        numerator.SetMinimum(numerator.GetBinContent(numerator.GetMinimumBin()))
    else:
        numerator.SetMaximum(max)
        numerator.SetMinimum(min)
    numerator.Draw('same colz')
    c1.Print(inputPath+year+signals[signal]+'_ratio_coupling_'+ratio+'_'+cut+'.pdf')

for cut in ['passNjOth', 'passMjjOth', 'SvBOnly', 'passSvB']:
    for tag in ['fourTag','threeTag']:
        YieldScan(cut,tag, max = 7.0)
for cut in [['SvBOnly','passNjOth'],['passMjjOth','passNjOth'],['passSvB','passMjjOth'],['passSvB','passNjOth']]:
    RatioScan(cut1=cut[0],cut2=cut[1],max = 1.0, min = 0.0)
for cut in ['passNjOth', 'passMjjOth', 'SvBOnly', 'passSvB']:
    RatioScan(cut1=cut,cut2=cut,tag1='fourTag',tag2='threeTag', auto = True)