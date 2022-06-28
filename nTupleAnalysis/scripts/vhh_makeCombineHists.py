#from bTagSyst import getBTagSFName
from ROOT import TFile, TH1F, TF1
import numpy as np
import sys
sys.path.insert(0, 'PlotTools/python/') #https://github.com/patrickbryant/PlotTools
from PlotTools import do_variable_rebinning
from os import path
from optparse import OptionParser

parser = OptionParser()

parser.add_option('-i', '--in',       dest="inFile",  default="")
parser.add_option('-n', '--name',     dest="histName",default="")
parser.add_option('--scale',          dest="scale",   default=None, help="Scale factor for hist")
parser.add_option('--errorScale',     dest="errorScale", default="1.0", help="Scale factor for hist stat error")
parser.add_option('-f', '--function', dest="function",default="", help="specified funtion will be used to scale the histogram along x dimension")
parser.add_option('-a', '--array',    dest="array",default="", help="specified array will be used to scale the histogram along x dimension")
parser.add_option(      '--syst',    dest="syst",default="", help="specified name of systematic hist")
parser.add_option(      '--debug',    dest="debug",   default=False,action="store_true", help="")
parser.add_option(      '--addHist',  dest="addHist", default=''   , help="path.root,path/to/hist,weight")

o, a = parser.parse_args()

def get(rootFile, path):
    obj = rootFile.Get(path)
    if obj == None:
        rootFile.ls()
        print 
        print "ERROR: Object not found -", rootFile, path
        sys.exit()

    else: return obj
 
#remove negative bins
zero = 0.00000001
def makePositive(hist):
    for bin in range(1,hist.GetNbinsX()+1):
        x   = hist.GetXaxis().GetBinCenter(bin)
        y   = hist.GetBinContent(bin)
        err = hist.GetBinError(bin)
        hist.SetBinContent(bin, y if y > 0 else zero)
        hist.SetBinError(bin, err if y > 0 else zero)


addHist = None
if o.addHist:
    addHistInfo = o.addHist.split(',')
    f = TFile(addHistInfo[0], 'READ')
    addHist = f.Get(addHistInfo[1])
    addHist.Scale(float(addHistInfo[2]))
    addHist.SetName('addHist')
    addHist.SetDirectory(0)
    f.Close()


print "input file:", o.inFile
f = TFile(o.inFile, "UPDATE")

def getAndStore(histName, suffix='', function='', array=''):
    h = get(f, histName)

    h.SetName(histName+ suffix)

    if o.errorScale is not None:
        for bin in range(1,h.GetNbinsX()+1):
            h.SetBinError(bin, h.GetBinError(bin)*float(o.errorScale))

    if function or array:
        xmin, xmax = h.GetXaxis().GetXmax(), h.GetXaxis().GetXmin()
        tf1, arr=None, None
        if function:
            tf1 = TF1('function', function, xmin, xmax)
        if array:
            arr = np.array(eval(array))

        for bin in range(1,h.GetNbinsX()+1):
            s = 1
            if function:
                l, u = h.GetXaxis().GetBinLowEdge(bin), h.GetXaxis().GetBinUpEdge(bin) #limits of integration
                w = h.GetBinWidth(bin) # divide intregral by bin width to get average of function over bin
                s = tf1.Integral(l,u)/w
            if array:
                s = arr[bin-1] # assume array at index i=bin-1 corresponds to bin 

            c, e = h.GetBinContent(bin), h.GetBinError(bin)
            h.SetBinContent(bin, c*s)
            h.SetBinError  (bin, e*s)

    makePositive(h)

    if o.scale is not None:
        h.Scale(float(o.scale))
    if addHist is not None:
        h.Add(addHist)

    f.cd()

    print 'write',h
    h.Write()

if o.debug: print 'getAndStore()'
getAndStore(o.histName, o.syst, function=o.function, array=o.array)
if o.debug: print 'got and stored'


f.Close()
