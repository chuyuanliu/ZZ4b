from copy import copy
from math import sqrt
import numpy as np
import ROOT
import re
import os, shutil
import getpass
import sys
import array
import json

sys.path.insert(0, '.')
import Helper.ROOTCanvas as canvas_helper

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning
# ROOT.gStyle.SetPalette(ROOT.kRainBow)
ROOT.gStyle.SetPalette(ROOT.kBird)
ROOT.gStyle.SetGridStyle(2)
ROOT.gStyle.SetHatchesLineWidth(1)

USER = getpass.getuser()
HIST_PATH = '/uscms/home/'+USER+'/nobackup/VHH/'
PLOT_FORMAT = '.pdf'
# PLOT_FORMAT = '.png'
USE_DENSITY = False
SKIP_EMPTY = False

# years = ['2016_preVFP', '2016_postVFP', '2016', '2017', '2018', 'RunII']
# years = ['RunII', '2016', '2017', '2018']
years = ['2016', '2017', '2018']
# years = ['RunII']
signals = ['ZHH', 'WHH', 'VHH']
# signals = ['VHH']
hists_filename = {
    'data'    : ['hists_j_r'],
    'ttbar'   : ['hists_j_r'],
    # 'mcs'     : {},
    'signal'  : ['hists', 'hists_jerUp', 'hists_jerDown', 'hists_jesTotalUp', 'hists_jesTotalDown'],
    # 'data'    : ['hists_j'],
    # 'ttbar'   : ['hists_j'],
    # 'mcs'    : {'VBF H->bb': 'VBFHToBB_M125_{year}/hists'},
    # 'signal'  : ['hists'],
}

# General

def integral(hist):
    n_bins = hist.GetNbinsX()
    total = hist.Integral(1, n_bins)
    return total

def integral_error(hist):
    n_bins = hist.GetNbinsX()
    error = ROOT.Double()
    total = hist.IntegralAndError(1, n_bins, error)
    return total, float(error)

def round_up(value, base):
    return int(value/base) * base + base

def get_ratio_range(max):
    diff = abs(1 - max)
    if diff < 0.05:
        return round_up(diff, 0.01)
    else:
        return round_up(diff, 0.05)

def reset_error(hist):
    for i in range(1, hist.GetNbinsX() + 1):
        hist.SetBinError(i, 0)

def rebin_hist(hist, rebin_x, rebin_y = None):
    if hist.GetSumw2N() == 0: hist.Sumw2()
    if rebin_y is None:
        rebin_y = rebin_x
    if isinstance(rebin_x, list):
        nbins = len(rebin_x) - 1
        bins = array.array('d', rebin_x)
        new_hist = hist.Rebin(nbins, hist.GetTitle()+'_rebinned', bins)
        if USE_DENSITY:
            bin_width = hist.GetBinWidth(1)
            bin_norm = new_hist.Clone()
            for i in range(1, nbins + 1):
                new_bin_width = bin_norm.GetBinWidth(i)
                bin_norm.SetBinContent(i, new_bin_width/bin_width)
                bin_norm.SetBinError(i, 0)
            new_hist.Divide(bin_norm)
        return new_hist
    elif isinstance(rebin_x, int):
        if isinstance(hist, ROOT.TH2):
            return hist.Rebin2D(rebin_x, rebin_y, hist.GetTitle()+'_rebinned')
        return hist.Rebin(rebin_x, hist.GetTitle()+'_rebinned')

class wildcard_match:
    def __init__(self, match_all_dirs = True, ignore_case = False, debug =False, cmd_length = 20):
        self.debug = debug
        self.cmd_length = cmd_length

        self.match_all_dirs = match_all_dirs
        self.flags = 0 | (re.IGNORECASE if ignore_case else 0)
    def match(self, pattern, string):
        return re.match('^' + re.escape(pattern).replace('\]', ')').replace('\[', '(').replace('\|', '|').replace('\*', '(.*?)') + '$', string, self.flags) is not None
    def match_path(self, pattern, path, match_all_dirs = None):
        if match_all_dirs is None:
            match_all_dirs = self.match_all_dirs
        if len(path) < len(pattern):
            return False
        elif len(path)!=len(pattern) and match_all_dirs:
            return False
        else:
            for i in range(len(pattern)):
                if not self.match(pattern[i], path[i]): 
                    return False
        return True

class path_extensions:
    def __init__(self, root, clean = False, debug =False, cmd_length = 20):
        self.debug = debug
        self.cmd_length = cmd_length

        self.user = getpass.getuser()
        self.root = root + ('' if root[-1] == '/' else '/')
        if clean and self.user in root and os.path.isdir(self.root):
            shutil.rmtree(self.root)
        if not os.path.isdir(self.root):
            os.mkdir(self.root)
    def mkdir(self, dirs):
        path = self.root
        if isinstance(dirs, list):
            for dir in dirs:
                path += dir + '/'
                if not os.path.isdir(path):
                    os.mkdir(path)
                    if self.debug: print('Create'.ljust(self.cmd_length) + path)
        return path
    def split(self, path):
        if len(path) > 0:
            if path[0] == '/':
                path = path[1:]
            if path[-1] == '/':
                path = path[:-1]
        return path.split('/')

# Physics    
# TODO VBF dataset=/VBF_HH_CV_*_C2V_*_C3_*_*-TuneC*_PSweights_13TeV-madgraph-pythia8/*/NANOAODSIM
class coupling_weight_generator:
    def __init__(self, basis = [], debug =False, cmd_length = 20):
        self.debug = debug
        self.cmd_length = cmd_length

        self.basis = []
        self.mat = None
        self.transmat = None # transformation matrix
        for coupling in basis:
            self.add_basis(**coupling)

    def get_str(self, num, point = '_'):
        return '{:.1f}'.format(num).replace('.', point)
    def get_filename(self, cv = 1.0, c2v = 1.0, c3 = 1.0, point = '_'):
        return '_CV_' + self.get_str(cv, point) + '_C2V_' + self.get_str(c2v, point) + '_C3_' + self.get_str(c3, point) + '_'
    def get_caption(self, cv = 1.0, c2v = 1.0, c3 = 1.0):
        return 'c_{V}' + self.get_str(cv,'.') + ' c_{2V}' + self.get_str(c2v,'.') + ' #kappa_{#lambda}' + self.get_str(c3,'.')

    def get_diagram_weight(self, cv = 1.0, c2v = 1.0, c3 = 1.0):
        return np.array([cv**2 * c3**2, cv**4, c2v**2, cv**3 * c3, cv * c3 * c2v, cv**2 * c2v])
    def get_transmat(self):
        count = len(self.basis)
        if count>=6:
            self.mat = np.empty((count, 6))
            for i in range(count):
                self.mat[i][:]=self.get_diagram_weight(**self.basis[i])
            self.transmat = np.linalg.pinv(self.mat)

    def get_all_filenames(self):
        return [self.get_filename(**coupling) for coupling in self.basis]
    def generate_weight(self, cv = 1.0, c2v = 1.0, c3 = 1.0):
        if self.transmat is not None:
            return np.round(np.matmul(self.get_diagram_weight(cv, c2v, c3), self.transmat), 15)
        
    def add_basis(self, cv = 1.0, c2v = 1.0, c3 = 1.0):
        self.basis.append({'cv':cv, 'c2v':c2v, 'c3':c3})
        self.get_transmat()

# Plot Rules

class plot_rule: #TEMP
    def __init__(self, patterns, operations):
        self.patterns = patterns
        self.operations = operations
        self.match = wildcard_match()
    def check(self, hist):
        for pattern in self.patterns:
            if not self.match.match(pattern[1],hist[pattern[0]]):
                return False
        return True
    def apply(self, hist_collection):
        for operation in self.operations:
            hist_collection.apply(operation)

# Plot

class histogram_1d_collection:
    '''data, multijet, ttbar, mcs, vhh, vbf'''
    # TODO vbf
    def __init__(self, path, title = '', tag = '', normalize = False, x_label = '', y_label = '', y_range = None, smooth = False, rules = [], event_count = False, no_legend = False):
        self.path = path
        self.title = title
        self.tag = tag
        self.normalize = normalize
        self.rules = rules
        self.event_count = event_count

        self.signals = {}
        self.data = None
        self.ttbar = None
        self.multijet = None
        self.other_bkg_mcs = []
        self.background_errors = []
        self.background = ROOT.THStack()

        self.legends = []
        self.no_legend = no_legend
        self.lines = 0

        self.x_max = float('-inf')
        self.x_min = float('inf')
        self.x_label = x_label
        self.y_max = float('-inf')
        self.y_min = 0
        self.y_label = y_label
        self.smooth = smooth
        self.y_range = y_range
        self.topmid_label = ''
        self.topright_label = ''

    def set_topright(self, label):
        self.topright_label = label

    def set_topmid(self, label):
        self.topmid_label = label

    def add_hist(self, hist, tag, scale = 1.0, line_color = 1):
        if not isinstance(hist, ROOT.TH1):
            return

        total, error = integral_error(hist)

        if total == 0.0 and SKIP_EMPTY:
            return
        is_bkg = 't#bar{t}' in tag or 'Multijet' in tag or tag.endswith(' MC')
        if self.normalize and not is_bkg:
            scale = 1.0 / total
        
        hist.Scale(scale)
        hist.SetLineColor(line_color)
        x_axis = hist.GetXaxis()
        y_axis = hist.GetYaxis()
        self.x_max = max(x_axis.GetXmax(), self.x_max)
        self.x_min = min(x_axis.GetXmin(), self.x_min)
        if not is_bkg:
            self.y_max = max(hist.GetMaximum(), self.y_max)
            self.y_min = min(hist.GetMinimum(), self.y_min)
        if self.x_label == '': self.x_label = x_axis.GetTitle()
        if self.y_label == '': self.y_label = y_axis.GetTitle()

        option = 'l'
        if 'Data' in tag:
            self.data = hist
            option = 'pe'
        elif tag == 't#bar{t}':
            self.ttbar = hist
            option = 'f'
        elif 'Multijet' in tag:
            self.multijet = hist
            option = 'f'
        elif tag.endswith(' MC'):
            self.other_bkg_mcs.append(hist)
            option = 'f'
        else:
            self.signals[tag] = hist
        if is_bkg and total > 0:
            style = len(self.background_errors) % 2
            error_hist = hist.Clone()
            error_hist.SetFillStyle(3125 if style else 3152)
            error_hist.SetFillColor(ROOT.kGray + 2)
            error_hist.SetMarkerSize(0)
            if len(self.background_errors) == 0:
                self.background_errors.append(error_hist)
            else:
                last = self.background_errors[-1].Clone()
                reset_error(last)
                error_hist.Add(last)
                self.background_errors.append(error_hist)
        label, lines = self.set_count(tag + ('' if scale == 1 or self.normalize else ' (#times' + str(scale) + ')'), total, error)
        self.lines += lines
        self.legends.append((hist, label, option))

    def set_font(self, text, num = 42):
        return '#font[' + str(num) + ']{' + text + '}'
    
    def set_count(self, label, count = 0, error = 0):
        if self.event_count and (not SKIP_EMPTY or (count != 0 and error != 0)) and not self.smooth:
            return '#splitline{' + label + '}{' + '{:.2f}'.format(count) + ' #pm ' + '{:.2f}'.format(error) + '}', 2
        else:
            return label, 1

    def plot(self, options = ''):
        background_scale = 1.0
        if self.normalize:
            total = 0.0
            if self.ttbar is not None:
                total += integral(self.ttbar)
            if self.multijet is not None:
                total += integral(self.multijet)
            for bkg in self.other_bkg_mcs:
                total += integral(bkg)
            if total != 0.0:
                background_scale = 1.0 / total
        if self.ttbar is not None:
            self.ttbar.SetFillColor(ROOT.kAzure-9)
            self.ttbar.Scale(background_scale)
            self.background.Add(self.ttbar)
        if self.multijet is not None:
            self.multijet.SetFillColor(ROOT.kYellow)
            self.multijet.Scale(background_scale)
            self.background.Add(self.multijet)
        colors = [ROOT.kMagenta-9, ROOT.kOrange-2, ROOT.kGreen+1, ROOT.kAzure+7, ROOT.kViolet-7, ROOT.kRed-4, ]
        for i, bkg in enumerate(self.other_bkg_mcs):
            bkg.SetFillColor(colors[i])
            bkg.Scale(background_scale)
            self.background.Add(bkg)
        if self.data is not None:
            self.data.SetMarkerColor(ROOT.kBlack)
            self.data.SetMarkerSize(1)
            self.data.SetMarkerStyle(8)  

        allow_ratio = (self.multijet is not None) and (self.ttbar is not None) and (self.data is not None) # TEMP     

        if not self.no_legend:
            legend_height = (0.04 if allow_ratio else 0.05) * self.lines * (1.33 if self.smooth else 1.0)
            self.legend = ROOT.TLegend(0.0, max(0.0, 0.95 - legend_height), 1.0, 0.95)
            self.legend.SetTextSize(0.06)
            self.legend.SetTextFont(42)
            self.legend.SetBorderSize(0)
            for legend in self.legends:
                self.legend.AddEntry(legend[0], legend[1], legend[2])

        self.y_max = max(self.background.GetMaximum(), self.y_max)
        self.y_min = min(self.background.GetMinimum(), self.y_min)
        if self.y_range is not None:
            self.y_min = self.y_range[0]
            self.y_max = self.y_range[1]
        for rule in self.rules:
            rule.apply(self)
        canvas_gen = canvas_helper.ROOTCanvas(self.x_min, self.x_max, self.y_min, self.y_max * 1.05)
        canvas_gen.TopMid.Text = self.set_font(self.topmid_label)
        canvas_gen.TopRight.Text = self.set_font(self.topright_label)
        canvas_gen.XLabel.Text = self.set_font(self.x_label)
        canvas_gen.YLabel.Text = self.set_font(self.y_label)
        canvas_gen.AllowLegend = not self.no_legend
        canvas_gen.AllowRatio  = allow_ratio
        canvas = canvas_gen.GetCanvas(self.title)
        canvas_gen.MainPad.cd()
        self.background.Draw('SAME HIST ' + options)
        for i in range(len(self.background_errors)):
            self.background_errors[i].Scale(background_scale)
            self.background_errors[i].Draw('SAME E2')
        if self.data is not None:
            self.data.Draw('SAME P E ' + options)
        temp = {} # TEMP
        for signal in self.signals:
            if self.smooth:
                if not self.no_legend: self.legend.SetTextSize(0.08) # TEMP
                self.signals[signal].Draw('SAME HIST PLC C') # TEMP
                temp[signal] = self.signals[signal].Clone() # TEMP
                temp[signal].SetMarkerSize(1) # TEMP
                temp[signal].SetMarkerStyle(8) # TEMP
                temp[signal].Draw('SAME X0 E1') # TEMP
            else:
                self.signals[signal].Draw('SAME HIST PLC ' + options)
        if not self.no_legend: 
            canvas_gen.Legend.cd()
            self.legend.Draw()
        if allow_ratio: # TEMP
            ratio_range = 0.1
            ratio = self.data.Clone()
            bkgd = self.ttbar.Clone()
            bkgd.Add(self.multijet)
            for bkg in self.other_bkg_mcs:
                bkgd.Add(bkg)
            bkgd_error = bkgd.Clone()
            n_bins = bkgd.GetNbinsX()
            for i in range(1, n_bins + 1):
                bkgd.SetBinError(i, 0)
            bkgd_error.Divide(bkgd)
            ratio.Divide(bkgd)
            ratio.SetMarkerSize(1)
            ratio.SetMarkerStyle(8) 
            canvas_gen.Ratio.cd()
            frame = canvas_gen.Ratio.DrawFrame(self.x_min, 1.0 - ratio_range, self.x_max, 1.0 + ratio_range)
            y_axis = frame.GetYaxis()
            y_axis.SetLabelSize(0.14)
            y_axis.SetNdivisions(2, 5, 0, False)
            x_axis = frame.GetXaxis()
            x_axis.SetLabelSize(0)
            canvas_gen.Ratio.SetGridy()
            label=ROOT.TLatex()
            label.SetTextSize(0.16)
            label.SetTextAngle(90)
            label.SetTextAlign(21)
            label.DrawLatex(canvas_gen.Var.GetX(-0.08), 1.0, self.set_font('Data/Bkgd.'))
            bkgd_error.SetFillStyle(3125)
            bkgd_error.SetFillColor(ROOT.kGray)
            bkgd_error.SetMarkerSize(0)
            bkgd_error.Draw('SAME E2')
            ratio.Draw('SAME X0 P E1')
            canvas_gen.Ratio.RedrawAxis()
        canvas_gen.MainPad.RedrawAxis()
        canvas.Print(self.path + self.tag + PLOT_FORMAT)

    def apply(self, action):
        exec(action)

class histogram_1d_syst:
    def __init__(self, path, title, tag = '', x_label = '', y_label = '', rules = None, labels = None):
        self.path = path
        self.title = title
        self.tag = tag
        self.rules = rules if rules else []
        self.labels = labels if labels else {'up':'Up', 'down':'Down', 'central':'Central'}
        self.systs = {}

        self.x_label = x_label
        self.y_label = y_label
        self.topmid_label = ''
        self.topright_label = ''

        self.x_max = {}
        self.x_min = {}
        self.y_max = {}
        self.y_min = {}
        self.colors = {'up':ROOT.kGreen+2, 'down':ROOT.kOrange-3}

    def set_topright(self, label):
        self.topright_label = label

    def set_topmid(self, label):
        self.topmid_label = label

    def set_font(self, text, num = 42):
        return '#font[' + str(num) + ']{' + text + '}'

    def add_hist(self, systs, tag):
        self.systs[tag] = systs

        self.x_max[tag] = float('-inf')
        self.x_min[tag] = float('inf')
        self.y_max[tag] = float('-inf')
        self.y_min[tag] = float('inf')

        for hist in systs.values(): 
            x_axis = hist.GetXaxis()
            y_axis = hist.GetYaxis()

            if self.x_label == '': self.x_label = x_axis.GetTitle()
            if self.y_label == '': self.y_label = y_axis.GetTitle()

            self.x_max[tag] = max(x_axis.GetXmax(), self.x_max[tag])
            self.x_min[tag] = min(x_axis.GetXmin(), self.x_min[tag])
            self.y_max[tag] = max(hist.GetMaximum(), self.y_max[tag])
            self.y_min[tag] = min(hist.GetMinimum(), self.y_min[tag])

    def apply(self, action):
        exec(action)
        
    def plot(self):
        for rule in self.rules:
            rule.apply(self)
        for tag in self.systs:
            canvas_gen = canvas_helper.ROOTCanvas(self.x_min[tag], self.x_max[tag], self.y_min[tag], self.y_max[tag] * 1.05)
            canvas_gen.TopMid.Text = self.set_font(self.topmid_label)
            canvas_gen.TopRight.Text = self.set_font(self.topright_label)
            canvas_gen.XLabel.Text = self.set_font(self.x_label)
            canvas_gen.YLabel.Text = self.set_font(self.y_label)
            canvas_gen.AllowLegend = True
            canvas_gen.AllowRatio  = True
            canvas = canvas_gen.GetCanvas(self.title + tag)
            canvas_gen.MainPad.cd()

            self.systs[tag]['up'].SetLineColor(self.colors['up'])
            self.systs[tag]['up'].Draw('SAME HIST')
            self.systs[tag]['down'].SetLineColor(self.colors['down'])
            self.systs[tag]['down'].Draw('SAME HIST')
            self.systs[tag]['central'].SetLineColor(ROOT.kBlack)
            self.systs[tag]['central'].Draw('SAME HIST')
            canvas_gen.MainPad.RedrawAxis()
            
            canvas_gen.Legend.cd()
            self.legend = ROOT.TLegend(0.0, max(0.0, 0.95 - 0.12), 1.0, 0.95)
            self.legend.SetTextSize(0.06)
            self.legend.SetTextFont(42)
            self.legend.SetBorderSize(0)
            for label in ['central', 'up', 'down']:
                self.legend.AddEntry(self.systs[tag][label], self.labels[label], 'pe')
            self.legend.Draw()

            canvas_gen.Ratio.cd()
            central = self.systs[tag]['central'].Clone()
            central_error = central.Clone()
            for i in range(1, central.GetNbinsX() + 1):
                central.SetBinError(i, 0)
            central_error.Divide(central)
            central_error.SetFillStyle(3125)
            central_error.SetFillColor(ROOT.kGray)
            central_error.SetMarkerSize(0)
            ratio = {}
            ratio_range = 0
            for shift in ['up', 'down']:
                ratio[shift] = self.systs[tag][shift].Clone()
                ratio[shift].Divide(central)
                ratio[shift].SetMarkerSize(1)
                ratio[shift].SetMarkerStyle(8) 
                ratio[shift].SetMarkerColor(self.colors[shift]) 
                ratio_range = max(ratio_range, get_ratio_range(ratio[shift].GetMaximum()))
                ratio_range = max(ratio_range, get_ratio_range(ratio[shift].GetMinimum()))
            frame = canvas_gen.Ratio.DrawFrame(self.x_min[tag], 1.0 - ratio_range, self.x_max[tag], 1.0 + ratio_range)
            y_axis = frame.GetYaxis()
            y_axis.SetLabelSize(0.14)
            y_axis.SetNdivisions(2, 5, 0, False)
            x_axis = frame.GetXaxis()
            x_axis.SetLabelSize(0)
            canvas_gen.Ratio.SetGridy()
            label=ROOT.TLatex()
            label.SetTextSize(0.10)
            label.SetTextAngle(90)
            label.SetTextAlign(21)
            label.DrawLatex(canvas_gen.Var.GetX(-0.08), 1.0, self.set_font('{up}({down})/{central}'.format(**self.labels)))
            central_error.Draw('SAME E2')
            for shift in ['up', 'down']:
                ratio[shift].Draw('SAME X0 P E1')
            canvas_gen.Ratio.RedrawAxis()
            canvas.Print(self.path + tag + self.tag + PLOT_FORMAT)

       
class histogram_2d_collection:
    def __init__(self, path, title, tag = '', x_label = '', y_label = '', z_label = '', contour = None):
        self.path = path
        self.title = title
        self.tag = tag

        self.hists = {}
        self.curves = []

        self.x_label = x_label
        self.y_label = y_label
        self.z_label = z_label

        self.x_max = float('-inf')
        self.x_min = float('inf')
        self.y_max = float('-inf')
        self.y_min = float('inf')
        self.contour = None if contour is None else array.array('d', contour)

    def add_curve(self, curve, levels = [], range = [None, None], color = ROOT.kRed):
        if len(levels) == 0:
            x_min = self.x_min if range[0] is None else max(self.x_min, range[0])
            x_max = self.x_max if range[1] is None else min(self.x_max, range[1])
            curve = ROOT.TF1('range', curve, x_min, x_max)
            curve.SetNpx(1000)
            curve.SetLineColor(color)
            self.curves.append(curve)
        else:
            curve = ROOT.TF2('range', curve, self.x_min, self.x_max, self.y_min, self.y_max)
            contour = array.array('d')
            for level in levels:
                contour.append(level)
            curve.SetContour(len(levels), contour)
            curve.SetNpx(1000)
            curve.SetNpy(1000)
            curve.SetLineColor(color)
            self.curves.append(curve)

    def add_hist(self, hist, tag):
        if not isinstance(hist, ROOT.TH2):
            return

        self.hists[tag] = hist
        x_axis = hist.GetXaxis()
        y_axis = hist.GetYaxis()
        z_axis = hist.GetZaxis()

        if self.x_label == '': self.x_label = x_axis.GetTitle()
        if self.y_label == '': self.y_label = y_axis.GetTitle()
        if self.z_label == '': self.z_label = z_axis.GetTitle()

        self.x_max = max(x_axis.GetXmax(), self.x_max)
        self.x_min = min(x_axis.GetXmin(), self.x_min)
        self.y_max = max(y_axis.GetXmax(), self.y_max)
        self.y_min = min(y_axis.GetXmin(), self.y_min)

    def plot(self, options = 'COLZ'):
        for tag in self.hists:
            canvas = ROOT.TCanvas(self.title + tag, self.title, 1000, 800)
            if self.contour is not None:
                self.hists[tag].SetContour(len(self.contour), self.contour)
                self.hists[tag].SetMaximum(self.contour[-1])
                self.hists[tag].SetMinimum(self.contour[0])
                title = self.hists[tag].GetTitle()
                title = '/'.join(title.split('/')[:-1] + [tag])
                self.hists[tag].SetTitle(title)
            self.hists[tag].SetTitle('')
            self.hists[tag].Draw(options)
            for curve in self.curves:
                curve.Draw('SAME')
            canvas.RedrawAxis()
            canvas.Print(self.path + tag + self.tag + PLOT_FORMAT)


class systematic:
    signals = {'VHH', 'ZHH', 'WHH'}
    def __init__(self, pattern = '', name = '', filename = None, signal = None):
        self.pattern  = pattern
        self.name     = name
        self.filename = filename
        self.signal   = signal
    def check_signal(self, signal):
        if self.signal is None and signal in self.signals:
            return True
        return signal in self.signal
    def get_name(self):
        return self.name
    def get_hist(self, hist):
        syst_hist = []
        for op in self.pattern:
            if isinstance(op, tuple):
                if isinstance(op[0], int):
                    if isinstance(op[1], int):
                        end = op[1] + 1
                        if op[1] == -1:
                            end = len(hist)
                        for i in range(op[0], end):
                            syst_hist.append(hist[i])
                    if isinstance(op[1], basestring):
                        strops = op[1].split('/')
                        i = 0
                        syst_hist_last = hist[op[0]]
                        while i < len(strops):
                            if strops[i][0] == '+':
                                syst_hist_last = strops[i][1:].format(syst_hist_last)
                                i += 1
                            elif strops[i][0] == '=':
                                syst_hist_last = syst_hist_last.replace(strops[i+1], strops[i][1:])
                                i += 2
                        syst_hist.append(syst_hist_last)
            elif isinstance(op, list):
                for i in op:
                    syst_hist.append(hist[i])
            elif isinstance(op, basestring):
                syst_hist.append(op)
        return self.filename, syst_hist

class plots:
    def __init__(self, basis = None, plot_dir = 'plots', match_all_dirs = True, ignore_case = True, debug = False, cmd_length =20):
        self.lumi = {'2016':  '36.3/fb',#35.8791
                    '2016_preVFP': '19.5/fb',
                    '2016_postVFP': '16.5/fb',
                    '2017':  '36.7/fb',#36.7338
                    '2018':  '59.8/fb',#59.9656
                    '17+18': '96.7/fb',
                    'RunII':'132.8/fb',
                    }

        self.debug = debug
        self.cmd_length = cmd_length

        self.input = HIST_PATH
        self.plot_dir = plot_dir
        out_path = HIST_PATH + self.plot_dir + '/' if self.plot_dir[-1] != '/' else ''
        self.output = out_path
        if not os.path.isdir(self.output):
            os.mkdir(self.output)
        self.years = years
        self.signals = signals
        self.other_mcs = list(hists_filename['mcs'].keys())

        self.path = {}
        self.all_hists = {}
        self.plot_hists = {}
        self.plot_couplings = []

        self.signal_files = {}
        self.data_files_4b = {}
        self.data_files_3b = {}
        self.ttbar_files_4b = {}
        self.ttbar_files_3b = {}
        self.multijet_files = {}
        self.other_mc_files = {}

        self.data_filename = hists_filename['data']
        self.ttbar_filename = hists_filename['ttbar']
        self.other_mc_filename = hists_filename['mcs']
        self.signal_filename = hists_filename['signal']

        self.plot_rules = []
        if basis is None: vhh_basis = [{},{'cv':0.5},{'cv':1.5},{'c2v':0.0},{'c2v':2.0},{'c3':0.0},{'c3':2.0},{'c3':20.0}]
        self.vhh_couplings = coupling_weight_generator(basis = vhh_basis, debug = self.debug, cmd_length = self.cmd_length)
        vbf_basis = [{},{'cv':0.5},{'cv':1.5},{'c2v':0.0},{'c2v':2.0},{'c3':0.0},{'c3':2.0}]
        self.vbf_couplings = coupling_weight_generator(basis = vbf_basis, debug = self.debug, cmd_length = self.cmd_length)

        self.match = wildcard_match(match_all_dirs, ignore_case, debug = self.debug, cmd_length = self.cmd_length)
        self.base_path = path_extensions(self.output, clean = True, debug = self.debug, cmd_length = self.cmd_length)

        # options
        self.no_background = False
        self.no_multijet = False
        self.no_signal = (len(self.signal_filename) == 0)
        self.no_Data = True
        self.mc_only = False
        self.mc_signals = False
        self.event_count = True
        self.signal_scale = 1
        
        for year in self.years:
            self.signal_files[year] = {}
            self.path[year] = {}
            for signal in self.signals:
                self.signal_files[year][signal] = {}
                for filename in self.signal_filename:
                    self.signal_files[year][signal][filename] = []
                self.path[year][signal] = path_extensions(self.output + year + signal + '/', clean = True, debug = self.debug, cmd_length = self.cmd_length)
            self.data_files_4b[year] = {}
            self.data_files_3b[year] = {}
            self.ttbar_files_4b[year] = {}
            self.ttbar_files_3b[year] = {}
            self.other_mc_files[year] = {}

        for year in self.years:
            for filename in self.data_filename:
                self.data_files_4b[year][filename] = ROOT.TFile(self.input + 'data' + year + '_4b/' + filename + '.root', 'READ')
                self.data_files_3b[year][filename] = ROOT.TFile(self.input + 'data' + year + '_3b/' + filename + '.root', 'READ')
            for filename in self.ttbar_filename:
                self.ttbar_files_4b[year][filename] = ROOT.TFile(self.input + 'TT' + year + '_4b/' + filename + '.root', 'READ')
                self.ttbar_files_3b[year][filename] = ROOT.TFile(self.input + 'TT' + year + '_3b/' + filename + '.root', 'READ')
            for mc_tag, filename in self.other_mc_filename.items():
                self.other_mc_files[year][mc_tag] = ROOT.TFile(self.input + filename.format(year = year) + '.root', 'READ')
            for filename in self.signal_filename:
                for signal in self.signals:
                    for coupling in self.vhh_couplings.get_all_filenames():
                        root_path = self.input + signal + 'To4B' + coupling + year + '/' + filename + '.root'
                        if os.path.isfile(root_path):
                            self.signal_files[year][signal][filename].append(ROOT.TFile(root_path, 'READ'))
                        else:
                            print('Error'.ljust(self.cmd_length) + 'file not found ' + root_path)
                            self.signal_files[year][signal][filename].append(None)
        if self.no_signal:
            self.root_dir = self.data_files_4b[self.years[0]][self.ttbar_filename[0]].GetDirectory('')
        else:
            self.root_dir = self.signal_files[self.years[0]][self.signals[0]][self.signal_filename[0]][0].GetDirectory('')
        self.modify_plot_hists_list_recursive('', self.initialize_hist)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        os.system('tar -C ' + self.input + ' -cvf ' + self.input + '{dir}.tar.gz {dir}/'.format(dir = self.plot_dir))
        for year in self.years:
            for filename in self.data_filename:
                if self.data_files_4b[year][filename] is not None:
                    if self.debug: print('Close'.ljust(self.cmd_length) + self.data_files_4b[year][filename].GetName())
                    self.data_files_4b[year][filename].Close()
                if self.data_files_3b[year][filename] is not None:
                    if self.debug: print('Close'.ljust(self.cmd_length) + self.data_files_3b[year][filename].GetName())
                    self.data_files_3b[year][filename].Close()
            for filename in self.ttbar_filename:
                if self.ttbar_files_4b[year][filename] is not None:
                    if self.debug: print('Close'.ljust(self.cmd_length) + self.ttbar_files_4b[year][filename].GetName())
                    self.ttbar_files_4b[year][filename].Close()
                if self.ttbar_files_3b[year][filename] is not None:
                    if self.debug: print('Close'.ljust(self.cmd_length) + self.ttbar_files_3b[year][filename].GetName())
                    self.ttbar_files_3b[year][filename].Close()         
            for signal in self.signals:
                for filename in self.signal_filename:
                    for file in self.signal_files[year][signal][filename]:
                        if file is not None:
                            if self.debug: print('Close'.ljust(self.cmd_length) + file.GetName())
                            file.Close()

    # internal methods

    ## path operation

    def get_hist_path(self, hist):
        if ':' in hist:
            path = hist.split(':')
            return path[0], path[1]
        else:
            return None, hist

    def join_hist_path(self, path):
        return '/'.join(path)

    ## hists operation

    def sum_hists(self, hists, weights):
        sum = hists[0].Clone()
        sum.Scale(weights[0])
        for i in range(1,len(hists)):
            sum.Add(hists[i],weights[i])       
        return sum

    def load_signal_mc_hists(self, year, signal, hist, rebin_x = 1, rebin_y = None, filename = None):
        hists = []
        if filename is None:
            filename = self.signal_filename[0]
        for file in self.signal_files[year][signal][filename]:
            if file is None:
                return None
            else:
                signal = rebin_hist(file.Get(hist), rebin_x, rebin_y)
                hists.append(signal)
        return hists

    def load_other_mc_hists(self, mc, year, hist, rebin_x = 1, rebin_y = None):
        if self.other_mc_files[year][mc] is None:
            return None
        mc = rebin_hist(self.other_mc_files[year][mc].Get(hist), rebin_x, rebin_y)
        return mc

    def load_ttbar_mc_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if 'fourTag' in hist:
            return self.load_ttbar_4b_hists(year, hist, rebin_x, rebin_y, filename)
        elif 'threeTag' in hist:
            return self.load_ttbar_3b_hists(year, hist, rebin_x, rebin_y, filename)

    def load_ttbar_4b_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if filename is None:
            filename = self.ttbar_filename[0]
        if self.ttbar_files_4b[year][filename] is None:
            return None
        ttbar = rebin_hist(self.ttbar_files_4b[year][filename].Get(hist), rebin_x, rebin_y)
        return ttbar
    
    def load_ttbar_3b_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if filename is None:
            filename = self.ttbar_filename[0]
        if self.ttbar_files_3b[year][filename] is None:
            return None
        ttbar = rebin_hist(self.ttbar_files_3b[year][filename].Get(hist), rebin_x, rebin_y)
        return ttbar

    def load_data_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if 'fourTag' in hist:
            return self.load_data_4b_hists(year, hist, rebin_x, rebin_y, filename)
        elif 'threeTag' in hist:
            return self.load_data_3b_hists(year, hist, rebin_x, rebin_y, filename)

    def load_data_4b_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if filename is None:
            filename = self.data_filename[0]
        if self.data_files_4b[year][filename] is None:
            return None
        data = rebin_hist(self.data_files_4b[year][filename].Get(hist), rebin_x, rebin_y)
        return data

    def load_data_3b_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if filename is None:
            filename = self.data_filename[0]
        if self.data_files_3b[year][filename] is None:
            return None
        data = rebin_hist(self.data_files_3b[year][filename].Get(hist), rebin_x, rebin_y)
        return data

    def load_multijet_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if filename is None:
            filename = self.data_filename[0]
        if self.data_files_3b[year][filename] is None:
            return None
        path = copy(self.all_hists[hist])
        path[1] = 'threeTag'
        path = self.join_hist_path(path)
        if filename == 'hists_j':
            hist_multijet = self.data_files_3b[year][filename].Get(path).Clone()
            if hist_multijet.GetSumw2N() == 0: hist_multijet.Sumw2()
            hist_ttbar = self.ttbar_files_3b[year][filename].Get(path).Clone()
            if hist_ttbar.GetSumw2N() == 0: hist_ttbar.Sumw2()
            hist_multijet.Add(hist_ttbar, -1)
            hist_multijet = rebin_hist(hist_multijet, rebin_x, rebin_y)
            return hist_multijet
        else:
            multijet = rebin_hist(self.data_files_3b[year][filename].Get(path), rebin_x, rebin_y)
            return multijet

    ## hists list

    def add_hist(self, hist, normalize = False):
        if hist not in self.plot_hists and hist in self.all_hists:
            self.plot_hists[hist] = normalize
            if self.debug: print('Add'.ljust(self.cmd_length) + hist)

    def remove_hist(self, hist, normalize = False):
        if hist in self.plot_hists:
            del self.plot_hists[hist]
            if self.debug: print('Remove'.ljust(self.cmd_length) + hist) 

    def initialize_hist(self, path):
        self.all_hists[path] = self.base_path.split(path)   

    def modify_plot_hists_list(self, patterns, operation, match_all_dirs = None, normalize = False):
        if isinstance(patterns, basestring):
            patterns = [self.base_path.split(patterns)]
        else:
            patterns = [self.base_path.split(pattern) for pattern in patterns]
        paths = self.all_hists.keys()
        for i in range(len(paths)):
            path = self.all_hists[paths[i]]
            for pattern in patterns:
                if self.match.match_path(pattern, path, match_all_dirs):
                    operation(paths[i], normalize)

    def modify_plot_hists_list_recursive(self, path, operation):
        current_dir = self.root_dir.GetDirectory(path)
        if current_dir:
            for file in current_dir.GetListOfKeys():
                self.modify_plot_hists_list_recursive(os.path.join(path, file.GetName()), operation)
        else:
            operation(path)
    
    # public methods      

    def debug_mode(self, debug):
        self.debug = debug
        self.vhh_couplings.debug = debug
        for year in self.years:
            for signal in self.signals:
                self.path[year][signal].debug = debug
        self.base_path.debug = debug
        self.match.debug = debug

    def add_dir(self, patterns, normalize = False):
        self.modify_plot_hists_list(patterns, self.add_hist, False, normalize = normalize)
            
    def remove_dir(self, patterns):
        self.modify_plot_hists_list(patterns, self.remove_hist, False)

    def add_hists(self, patterns, normalize = False):
        self.modify_plot_hists_list(patterns, self.add_hist, normalize = normalize)

    def remove_hists(self, patterns):
        self.modify_plot_hists_list(patterns, self.remove_hist)

    def clear_hists(self):
        self.plot_hists = {}

    def add_couplings(self, cv = 1.0, c2v = 1.0, c3 = 1.0):
        if not isinstance(cv, list): cv = [cv]
        if not isinstance(c2v, list): c2v = [c2v]
        if not isinstance(c3, list): c3 = [c3]
        for cv_iter in cv:
            for c2v_iter in c2v:
                for c3_iter in c3:
                    self.plot_couplings.append({'cv':cv_iter, 'c2v':c2v_iter, 'c3':c3_iter})
    def clear_couplings(self):
        self.plot_couplings = []
    def add_plot_rule(self, rule):
        self.plot_rules.append(rule)

    def plot_1d(self, rebin = 1, options = ''):
        '''data, multijet, ttbar, mcs, vhh, vbf'''
        # TODO vbf
        for year in self.years:
            for signal in self.signals:
                for hist in self.plot_hists:
                    if self.debug: print('Plot'.ljust(self.cmd_length) + hist) 
                    rules = []
                    for rule in self.plot_rules:
                        if rule.check(self.all_hists[hist]):
                            rules.append(rule)
                    path = self.path[year][signal].mkdir(self.all_hists[hist][:-1])
                    path += self.all_hists[hist][-1]
                    ploter = histogram_1d_collection(path, title=hist, normalize = self.plot_hists[hist],y_label='Events',rules=rules, event_count=self.event_count)
                    if not self.no_Data and not self.mc_only:
                        ploter.add_hist(self.load_data_hists(year, hist, rebin), 'Data ' + self.lumi[year] + ' ' + year)
                    if not self.no_background:
                        ploter.add_hist(self.load_ttbar_mc_hists(year, hist, rebin), 't#bar{t}')
                        if not self.mc_only and not self.no_multijet:
                            ploter.add_hist(self.load_multijet_hists(year, hist, rebin), 'Multijet Model')
                    for mc in self.other_mcs:
                        ploter.add_hist(self.load_other_mc_hists(mc, year, hist, rebin), mc + ' MC')
                    if not self.no_signal:
                        signal_mc = self.load_signal_mc_hists(year, signal, hist, rebin)
                    else:
                        signal_mc = None                        
                    if signal_mc is not None:
                        if self.mc_signals: 
                            for i,coupling in enumerate(self.vhh_couplings.basis):
                                ploter.add_hist(signal_mc[i], self.vhh_couplings.get_caption(**coupling), self.signal_scale)
                        else:
                            for coupling in self.plot_couplings:
                                weights = self.vhh_couplings.generate_weight(**coupling)
                                ploter.add_hist(self.sum_hists(signal_mc, weights), self.vhh_couplings.get_caption(**coupling), self.signal_scale)
                    ploter.plot(options)
        self.clear_hists()

    def plot_1d_animation(self, rebin = 1, options = '', tag = ''): #TEMP
        for year in self.years:
            for signal in self.signals:
                for hist in self.plot_hists:
                    if self.debug: print('Plot'.ljust(self.cmd_length) + hist) 
                    rules = []
                    for rule in self.plot_rules:
                        if rule.check(self.all_hists[hist]):
                            rules.append(rule)
                    path = self.path[year][signal].mkdir(self.all_hists[hist])
                    signal_mc = self.load_signal_mc_hists(year, signal, hist, rebin)
                    log = ''
                    for i,coupling in enumerate(self.plot_couplings):
                        ploter = histogram_1d_collection(path+'/'+tag+str(i), title=self.vhh_couplings.get_caption(**coupling), normalize = self.plot_hists[hist],y_label='Events',rules=rules, event_count=self.event_count, no_legend = True)
                        weights = self.vhh_couplings.generate_weight(**coupling)
                        ploter.add_hist(self.sum_hists(signal_mc, weights), self.vhh_couplings.get_caption(**coupling), self.signal_scale)
                        ploter.plot(options)
                        log += 'file {}.png\nduration 00:00:00.150\n'.format(tag+str(i))
                    with open(path + tag + '.txt', 'w') as f:
                        f.write(log)
        self.clear_hists()
        self.clear_couplings()

    def compare_histfile(self, pattern, histTags, rebin = 1, normalize = False, extra_tag = ''):
        hists = []
        def add_compare_hists(path, norm):
            hists.append(path)
        self.modify_plot_hists_list(pattern, add_compare_hists)
        histFiles_sig = {}
        histFiles_bkg = {}
        for tag in histTags.keys():
            histFiles_sig[tag.format(self.signal_filename[0])] = histTags[tag]
            histFiles_bkg[tag.format(self.data_filename[0])] = histTags[tag]
        for hist in hists:
            for year in self.years:
                for signal in self.signals:
                    rules = []
                    for rule in self.plot_rules:
                        if rule.check(self.all_hists[hist]):
                            rules.append(rule)
                    if self.debug: print('Plot'.ljust(self.cmd_length) + hist) 
                    signal_mc = {}
                    ttbar_mc  = {}
                    multijet  = {}
                    for file in histFiles_sig.keys():
                        signal_mc[file] = self.load_signal_mc_hists(year, signal, hist, rebin, filename = file)
                    for file in histFiles_bkg.keys():
                        ttbar_mc[file]  = self.load_ttbar_mc_hists(year, hist, rebin, filename = file)
                        multijet[file]  = self.load_multijet_hists(year, hist, rebin, filename = file)
                    hist_dir = copy(self.all_hists[hist])
                    hist_dir[-1] = hist_dir[-1] + extra_tag
                    path = self.path[year][signal].mkdir(hist_dir)
                    if self.mc_signals: 
                        for i,coupling in enumerate(self.vhh_couplings.basis):
                            couplingName = self.vhh_couplings.get_filename(**coupling)[1:-1]
                            ploter = histogram_1d_collection(path + couplingName, title=hist, normalize = normalize, y_label='Events', rules=rules, event_count=self.event_count)
                            for file in histFiles_sig.keys():
                                ploter.add_hist(signal_mc[file][i], histFiles_sig[file])
                            ploter.plot()
                    else:
                        for coupling in self.plot_couplings:
                            couplingName = self.vhh_couplings.get_filename(**coupling)[1:-1]
                            ploter = histogram_1d_collection(path + couplingName, title=hist, normalize = normalize, y_label='Events', rules=rules, event_count=self.event_count)
                            weights = self.vhh_couplings.generate_weight(**coupling)
                            for file in histFiles_sig.keys():
                                ploter.add_hist(self.sum_hists(signal_mc[file], weights), histFiles_sig[file])
                            ploter.plot()
                    ploter = histogram_1d_collection(path + 'ttbar', title=hist, normalize = normalize, y_label='Events', rules=rules, event_count=self.event_count)
                    for file in histFiles_bkg.keys():
                        ploter.add_hist(ttbar_mc[file], histFiles_bkg[file])
                    ploter.plot()
                    ploter = histogram_1d_collection(path + 'multijet', title=hist, normalize = normalize, y_label='Events', rules=rules, event_count=self.event_count)
                    for file in histFiles_bkg.keys():
                        ploter.add_hist(multijet[file], histFiles_bkg[file])
                    ploter.plot()
        
    def plot_syst(self, pattern, systs, tag = '', rebin = 1, labels = None):
        hists = []
        def add_syst_hist(path, norm):
            hists.append(path)
        self.modify_plot_hists_list(pattern, add_syst_hist)
        for hist in hists:
            for year in self.years:
                for signal in self.signals:
                    rules = []
                    for rule in self.plot_rules:
                        if rule.check(self.all_hists[hist]):
                            rules.append(rule)
                    if self.debug: print('Plot'.ljust(self.cmd_length) + hist) 
                    signal_mc = {}
                    for syst in systs:
                        syst_hist_file, syst_hist = systs[syst].get_hist(self.all_hists[hist])
                        signal_mc[syst] = self.load_signal_mc_hists(year, signal, self.join_hist_path(syst_hist), rebin, filename = syst_hist_file)
                    hist_path = copy(self.all_hists[hist])
                    hist_path[-1] = hist_path[-1]+tag
                    path = self.path[year][signal].mkdir(hist_path)
                    ploter = histogram_1d_syst(path, title=hist, rules=rules, labels=labels)           
                    if self.mc_signals: 
                        for i,coupling in enumerate(self.vhh_couplings.basis):
                            signals = {}
                            for syst in systs:
                                signals[syst] = signal_mc[syst][i]
                            ploter.add_hist(signals, self.vhh_couplings.get_filename(**coupling)[1:-1])
                    else:
                        for coupling in self.plot_couplings:
                            signals = {}
                            weights = self.vhh_couplings.generate_weight(**coupling)
                            for syst in systs:
                                signals[syst] = self.sum_hists(signal_mc[syst], weights)
                            ploter.add_hist(signals, self.vhh_couplings.get_filename(**coupling)[1:-1])
                    ploter.plot()

    def plot_2d(self, options = 'COLZ'): #TEMP
        for year in self.years:
            for signal in self.signals:
                for hist in self.plot_hists:
                    if self.debug: print('Plot'.ljust(self.cmd_length) + hist) 
                    path = self.path[year][signal].mkdir(self.all_hists[hist])
                    ploter = histogram_2d_collection(path, title=hist)
                    if not self.no_Data and not self.mc_only:
                        ploter.add_hist(self.load_data_hists(year, hist), 'Data')
                    if not self.no_background:
                        ploter.add_hist(self.load_ttbar_mc_hists(year, hist), 'TTbar')
                        if not self.no_multijet and not self.mc_only:
                            ploter.add_hist(self.load_multijet_hists(year, hist), 'Multijet')
                    if not self.no_signal:
                        signal_mc = self.load_signal_mc_hists(year, signal, hist)
                        if not isinstance(signal_mc[0], ROOT.TH2):
                            continue
                    else:
                        signal_mc = None
                    if signal_mc is not None:
                        if self.mc_signals: 
                            for i,coupling in enumerate(self.vhh_couplings.basis):
                                ploter.add_hist(signal_mc[i], self.vhh_couplings.get_filename(**coupling)[1:-1])
                        else:
                            for coupling in self.plot_couplings:
                                weights = self.vhh_couplings.generate_weight(**coupling)
                                ploter.add_hist(self.sum_hists(signal_mc, weights), self.vhh_couplings.get_filename(**coupling)[1:-1])
                    if 'm4j' in hist and 'leadSt_dR' in hist:
                        ploter.add_curve('650.0/x+0.5', range=[None, 650])
                        ploter.add_curve('360.0/x-0.5')
                        ploter.add_curve('1.5', range = [650, None])
                    if 'm4j' in hist and 'sublSt_dR' in hist:
                        ploter.add_curve('650.0/x+0.7', range=[None, 812.5])
                        ploter.add_curve('235.0/x')
                        ploter.add_curve('1.5', range=[812.5, None])
                    if 'leadSt_m' in hist and 'sublSt_m' in hist:
                        ploter.add_curve('(((x-125*1.02)/(0.1*x))**2+((y-125*0.98)/(0.1*y))**2)',[1.9**2])
                        ploter.add_curve('((x-125*1.02)**2+(y-125*0.98)**2)',[30**2], color=ROOT.kGreen)
                        ploter.add_curve('((x-125*1.02)**2+(y-125*0.98)**2)',[25**2], color=ROOT.kBlue)
                    ploter.plot(options)
        self.clear_hists()

    def make_PUJetID_SF(self, denominators, numerators, sf_name, sf_category, others = {}, rebin_x = 1, rebin_y =1): #TEMP
        SFs = {}
        for year in self.years:
            SF_json = {}
            for i in range(len(sf_category)):
                category = sf_category[i]
                numerator = numerators[i]
                denominator = denominators[i]
                if self.debug: print('Plot'.ljust(self.cmd_length) + numerator)
                ttbar_num = self.load_ttbar_3b_hists(year, numerator, rebin_x, rebin_y)
                ttbar_den = self.load_ttbar_3b_hists(year, denominator, rebin_x, rebin_y)
                ttbar_eff = ttbar_num.Clone()
                ttbar_eff.Divide(ttbar_den)
                data_num = self.load_data_3b_hists(year, numerator, rebin_x, rebin_y)
                data_den = self.load_data_3b_hists(year, denominator, rebin_x, rebin_y)
                data_eff = data_num.Clone()
                data_eff.Divide(data_den)
                SFs[category] = data_eff.Clone()
                SFs[category].Divide(ttbar_eff)
                SFs_up = SFs[category].Clone()
                SFs_down = SFs[category].Clone()
                x_bins = SFs[category].GetNbinsX()
                y_bins = SFs[category].GetNbinsY()
                for x_bin in range(x_bins + 2):
                    for y_bin in range(y_bins + 2):
                        SFs_up.SetBinContent(x_bin, y_bin, SFs_up.GetBinContent(x_bin, y_bin) + SFs_up.GetBinErrorUp(x_bin, y_bin))
                        SFs_down.SetBinContent(x_bin, y_bin, SFs_down.GetBinContent(x_bin, y_bin) - SFs_down.GetBinErrorLow(x_bin, y_bin))
                x_axis = SFs[category].GetXaxis()
                y_axis = SFs[category].GetYaxis()
                if SFs[category].Integral()>0:
                    SF_json[category] = {}
                    SF_data = SF_json[category]
                    SF_data['pt']  = []
                    SF_data['eta'] = []
                    SF_data['sf'] = {}
                    SF_data['sf']['central']  = []
                    SF_data['sf']['up']  = []
                    SF_data['sf']['down']  = []
                    for y_bin in range(1, y_bins + 2):
                        SF_data['eta'].append(y_axis.GetBinLowEdge(y_bin))
                    for x_bin in range(1, x_bins + 2):
                        if x_axis.GetBinLowEdge(x_bin) >= 40:
                            SF_data['pt'].append(x_axis.GetBinLowEdge(x_bin))
                    for x_bin in range(1, x_bins + 1):
                        if x_axis.GetBinLowEdge(x_bin) >= 40:
                            for y_bin in range(1, y_bins + 1):
                                SF_data['sf']['central'].append(SFs[category].GetBinContent(x_bin, y_bin))
                                SF_data['sf']['up'].append(SFs_up.GetBinContent(x_bin, y_bin))
                                SF_data['sf']['down'].append(SFs_down.GetBinContent(x_bin, y_bin))
                path = self.path[year]['VHH'].mkdir([sf_name + '_' + category])
                ploter_count = histogram_2d_collection(path, title = category)
                ploter_efficiency = histogram_2d_collection(path, title = category, contour = np.concatenate(([0], np.arange(0.50,1.05,0.05))))
                ploter_sf = histogram_2d_collection(path, title = category, contour = np.concatenate(([0], np.arange(0.80,1.25,0.05), [2])))
                ttbar_others = {}
                data_others = {}
                for key in others:
                    ttbar_others[key] = self.load_ttbar_3b_hists(year, others[key])
                    ploter_count.add_hist(ttbar_others[key], 'ttbar_' + key)
                    data_others[key]  = self.load_data_3b_hists(year, others[key])
                    ploter_count.add_hist(data_others[key], 'data_' + key)
                if ttbar_num.Integral()>0: ploter_count.add_hist(ttbar_num, 'ttbar_numerator')
                if ttbar_den.Integral()>0: ploter_count.add_hist(ttbar_den, 'ttbar_denominator')
                if ttbar_eff.Integral()>0: ploter_efficiency.add_hist(ttbar_eff, 'ttbar_efficiency')
                if data_num.Integral()>0: ploter_count.add_hist(data_num, 'data_numerator')
                if data_den.Integral()>0: ploter_count.add_hist(data_den, 'data_denominator')
                if data_eff.Integral()>0: ploter_efficiency.add_hist(data_eff, 'data_efficiency')
                if SFs[category].Integral()>0: ploter_sf.add_hist(SFs[category], 'SF_central')
                if SFs_up.Integral()>0: ploter_sf.add_hist(SFs_up, 'SF_up')
                if SFs_down.Integral()>0: ploter_sf.add_hist(SFs_down, 'SF_down')
                ploter_count.plot('TEXT COLZ')
                ploter_efficiency.plot('TEXT COLZ')
                ploter_sf.plot('TEXT COLZ')
            with open(self.path[year]['VHH'].root + sf_name + year + '.json', 'w') as f:
                f.write(json.dumps(SF_json))
            for i in range(len(sf_category)):
                for j in range(i + 1, len(sf_category)):
                    SF_num = SFs[sf_category[i]].Clone()
                    SF_den = SFs[sf_category[j]]
                    if SF_num.Integral() * SF_den.Integral() > 0:
                        SF_num.Divide(SF_den)
                        path = self.path[year]['VHH'].mkdir([sf_name + '_' + sf_category[i] + '_' + sf_category[j]])
                        ploter = histogram_2d_collection(path, title = sf_category[j], contour = np.concatenate(([0], np.arange(0.80,1.25,0.05), [2])))
                        ploter.add_hist(SF_num, sf_category[i] + '_' + sf_category[j])
                        ploter.plot('TEXT COLZ')
    
    def save(self, filename = 'shapes', rebin = 1):
        save_path = path_extensions(self.input + 'save', clean = True, debug = self.debug, cmd_length = self.cmd_length)
        filename = '{path}{filename}.root'.format(path = save_path.root, filename = filename)
        file = ROOT.TFile(filename,'recreate')
        if self.debug: print('Create'.ljust(self.cmd_length) + filename) 
        for hist in self.plot_hists:
            file.cd()
            hist_name = hist.split('/')[-1]
            file.mkdir(hist_name)
            file.cd(hist_name)
            for year in self.years:
                for signal in self.signals:
                    if self.debug: print('Save'.ljust(self.cmd_length) + hist) 
                    signal_mc = self.load_signal_mc_hists(year, signal, hist, rebin)
                    if self.mc_signals: 
                        for i,coupling in enumerate(self.vhh_couplings.basis):
                            histname = '{signal}{coupling}{year}'.format(signal = signal, coupling = self.vhh_couplings.get_filename(**coupling), year = year)
                            signal_mc[i].SetNameTitle(histname, histname)
                            signal_mc[i].Write()
                    else:
                        for coupling in self.plot_couplings:
                            weights = self.vhh_couplings.generate_weight(**coupling)
                            coupling_signal = self.sum_hists(signal_mc, weights)
                            histname = '{signal}{coupling}{year}'.format(signal = signal, coupling = self.vhh_couplings.get_filename(**coupling), year = year)
                            coupling_signal.SetNameTitle(histname, histname)
                            coupling_signal.Write()


    def save_shape(self, filename, hist, MC_systs = [], rebin = 1, unblind = False, mix_as_obs = ''):
        for year in self.years:
            format_args = {'year': year}
            if self.debug: print('Datacard'.ljust(self.cmd_length) + filename.format(**format_args)) 
            output_file = ROOT.TFile(self.input + filename.format(**format_args) + '.root','recreate')                
            output_file.cd()
            multijet = self.load_multijet_hists(year, hist, rebin)
            mj_name = 'multijet_background'
            multijet.SetNameTitle(mj_name,mj_name+'_'+year)
            multijet.Write()
            for syst in MC_systs:
                if syst.check_signal(mj_name):
                    syst_hist_file, syst_hist = syst.get_hist(self.all_hists[hist])
                    mj_syst = self.load_multijet_hists(year, self.join_hist_path(syst_hist), rebin, filename = syst_hist_file)
                    suffix = mj_name+'_'+syst.get_name().format(**format_args)
                    mj_syst.SetNameTitle(suffix,suffix)
            ttbar = self.load_ttbar_mc_hists(year, hist, rebin)
            ttbar.SetNameTitle('ttbar_background','ttbar_background'+year)
            ttbar.Write()
            x_axis = ttbar.GetXaxis()
            if unblind:
                data = self.load_data_4b_hists(year, hist, rebin)
                data.SetNameTitle('data_obs', 'data_obs_'+year)
                data.Write()
            elif mix_as_obs:
                mix_file, mix_data = mix_as_obs.split(':')
                mix_file = ROOT.TFile(mix_file, 'READ')
                mix_data = rebin_hist(mix_file.Get(mix_data.format(year = year) + '/data_obs'), rebin)
                mix_data.SetNameTitle('data_obs', 'mix_data_obs_'+year)
                output_file.cd()
                mix_data.Write()
            else:
                data = ROOT.TH1F('data_obs','data_obs'+year+'; '+x_axis.GetTitle()+'; Events', ttbar.GetNbinsX(), x_axis.GetXmin(), x_axis.GetXmax() )
                data.Write()
            for signal in self.signals:
                signal_systs = {}
                for syst in MC_systs:
                    if syst.check_signal(signal):
                        syst_hist_file, syst_hist = syst.get_hist(self.all_hists[hist])
                        signal_systs[syst.get_name()] = self.load_signal_mc_hists(year, signal, self.join_hist_path(syst_hist), rebin, filename = syst_hist_file)
                signal_mc = self.load_signal_mc_hists(year, signal, hist, rebin)
                for i,coupling in enumerate(self.vhh_couplings.basis):
                    name = signal + self.vhh_couplings.get_filename(point= 'p', **coupling)[:-1].replace('C3', 'kl').replace('C2V', 'C2' + signal[0]) + '_hbbhbb'
                    name = name.replace('p0_','_')
                    signal_hist = signal_mc[i]
                    signal_hist.SetNameTitle(name,name+"_"+year)
                    signal_hist.Write()
                    for syst in signal_systs.keys():
                        suffix = name+'_'+syst.format(**format_args)
                        signal_systs[syst][i].SetNameTitle(suffix,suffix)
                        signal_systs[syst][i].Write()
            output_file.Close()

    def optimize(self, hist, steps = None, bound = None, step_to_x = None):
            for year in self.years:
                for signal in self.signals:
                    # input histograms
                    path = copy(self.all_hists[hist])
                    path[1] = 'fourTag'
                    path[3] = 'HHCR'
                    data_4b_CR = self.load_data_hists(year,self.join_hist_path(path))
                    tt_4b_CR = self.load_ttbar_mc_hists(year,self.join_hist_path(path))
                    path[3] = 'HHSR'
                    tt_4b_SR = self.load_ttbar_mc_hists(year,self.join_hist_path(path))
                    signal_mc = self.load_signal_mc_hists(year, signal, self.join_hist_path(path))
                    multijet_3b_SR_hist = self.load_multijet_hists(year,self.join_hist_path(path))
                    signal_4b_SR = {}
                    for coupling in self.plot_couplings:
                        weights = self.vhh_couplings.generate_weight(**coupling)
                        signal_4b_SR[self.vhh_couplings.get_caption(**coupling)] = self.sum_hists(signal_mc, weights)

                    # plot variables
                    x_axis = data_4b_CR.GetXaxis()
                    n_bins = data_4b_CR.GetNbinsX()
                    x_max = x_axis.GetXmax()
                    x_min = x_axis.GetXmin()
                    x_label = 'Cut on ' + x_axis.GetTitle()

                    # derived variables
                    hists_S_B = {}
                    hists_S_sqrtB = {}
                    multijet_4b_CR = integral(data_4b_CR) - integral(tt_4b_CR)
                    multijet_3b_SR = integral(multijet_3b_SR_hist)

                    # optimize range
                    # step = [0, steps - 1]
                    if steps is None:
                        steps = n_bins
                    def getBound(step):
                        return step + 1, steps
                    if bound is None:
                        bound = getBound
                    def getX(step):
                        return (x_max - x_min)/steps * step + x_min
                    if step_to_x is None:
                        step_to_x = getX

                        
                    # output histograms
                    signal_yield = {}
                    for coupling in signal_4b_SR:
                        hists_S_B[coupling] = ROOT.TH1F(coupling, '', steps, step_to_x(0), step_to_x(steps))
                        hists_S_B[coupling].SetXTitle(x_label)
                        hists_S_B[coupling].SetYTitle('S/B')
                        hists_S_sqrtB[coupling] = ROOT.TH1F(coupling, '', steps, step_to_x(0), step_to_x(steps))
                        hists_S_sqrtB[coupling].SetXTitle(x_label)
                        hists_S_sqrtB[coupling].SetYTitle('S/#sqrt{B}')
                        signal_yield[coupling] = ROOT.TH1F(coupling, '', steps, step_to_x(0), step_to_x(steps))
                        signal_yield[coupling].SetXTitle(x_label)
                        signal_yield[coupling].SetYTitle('Events')
                    tt_yield = ROOT.TH1F('ttbar', '', steps, step_to_x(0), step_to_x(steps))
                    tt_yield.SetXTitle(x_label)
                    tt_yield.SetYTitle('Events')
                    multijet_yield = ROOT.TH1F('multijet', '', steps, step_to_x(0), step_to_x(steps))
                    multijet_yield.SetXTitle(x_label)
                    multijet_yield.SetYTitle('Events')

                    for step in range(steps):
                        bin = step + 1
                        lower, upper = bound(step)
                        tt = tt_4b_SR.Integral(lower, upper)
                        multijet = multijet_3b_SR * (data_4b_CR.Integral(lower, upper) - tt_4b_CR.Integral(lower, upper))/ multijet_4b_CR
                        b = tt + multijet
                        tt_yield.SetBinContent(bin, tt)
                        multijet_yield.SetBinContent(bin, multijet)
                        for coupling in signal_4b_SR:
                            s = signal_4b_SR[coupling].Integral(lower, upper)
                            hists_S_B[coupling].SetBinContent(bin, s/b)
                            hists_S_sqrtB[coupling].SetBinContent(bin, s/sqrt(b))
                            signal_yield[coupling].SetBinContent(bin, s)

                    output_path = self.path[year][signal].mkdir(self.all_hists[hist][:-1])
                    output_path += self.all_hists[hist][-1]
                    ploter_S_B = histogram_1d_collection(output_path, title=hist, tag='_S_B')
                    ploter_S_sqrtB = histogram_1d_collection(output_path, title=hist, tag='_S_sqrtB')
                    ploter_yield = histogram_1d_collection(output_path, title='Signal & Background Yield', tag='_yield', event_count=self.event_count)
                    for coupling in signal_4b_SR:
                        ploter_S_B.add_hist(hists_S_B[coupling], coupling)
                        ploter_S_sqrtB.add_hist(hists_S_sqrtB[coupling], coupling)
                        ploter_yield.add_hist(signal_yield[coupling],coupling,5000)
                    ploter_yield.add_hist(tt_yield, 't#bar{t}')
                    ploter_yield.add_hist(multijet_yield, 'Multijet Model')
                    ploter_S_B.plot()
                    ploter_S_sqrtB.plot()
                    ploter_yield.plot()
                    if self.debug: print('Optimize'.ljust(self.cmd_length) + hist) 

    def GetAccxEff(self, h2d, cuts): #Temp
        relative = []
        absolute = []
        count = []
        denominatorZero = None
        for d in range(len(cuts)):
            denominator = cuts[d][0]
            den_name = cuts[d][1]
            b=h2d.GetYaxis().FindBin(denominator)
            hDenominator=h2d.ProjectionX(denominator, b, b)
            hSignal = hDenominator.Clone()
            hRatioAbs = hDenominator.Clone()
            if d == 0:
                denominatorZero = hSignal.Clone()
            hRatioAbs.Divide(denominatorZero)
            hRatioAbs.SetAxisRange(250, 1700)
            count.append((den_name, hSignal))
            absolute.append((den_name, hRatioAbs))
            if d+1< len(cuts):
                n = d+1
                numerator = cuts[n][0]
                num_name = cuts[n][1]
                b=h2d.GetYaxis().FindBin(numerator)
                hNumerator=h2d.ProjectionX(numerator, b, b)
                hRatioRel=ROOT.TH1D(hNumerator)
                hRatioRel.SetName(numerator+"_over_"+denominator)
                hRatioRel.SetAxisRange(250, 1700)
                hRatioRel.Divide(hDenominator)
                relative.append((num_name+" / "+den_name,hRatioRel))
        return relative, absolute, count

    def AccxEff(self, cuts):#Temp
        for year in self.years:
            for signal in self.signals:
                output_path = self.path[year][signal].mkdir(['AccxEff'])
                signal_mc = self.load_signal_mc_hists(year, signal, 'cutflow/fourTag/truthM4b')
                for coupling in self.plot_couplings:
                    title = self.vhh_couplings.get_filename(**coupling)[1:-1]
                    hist_path = output_path+title
                    ploter_acc_eff_rela = histogram_1d_collection(hist_path, title='Acc#times Eff ' + title, tag='AccxEff_relative',x_label='Truth m_{4b}', y_label='Relative Acceptance #times Efficiency', y_range=[0,1], smooth= True)
                    ploter_acc_eff = histogram_1d_collection(hist_path, title='Acc#times Eff ' + title, tag='AccxEff',x_label='Truth m_{4b}', y_label='Acceptance #times Efficiency', smooth=True)
                    ploter_acc_eff_count = histogram_1d_collection(hist_path, title='Acc#times Eff ' + title, tag='Count',x_label='Truth m_{4b}', y_label='Events', event_count = self.event_count)
                    weights= self.vhh_couplings.generate_weight(**coupling)
                    h2d = self.sum_hists(signal_mc, weights)
                    relative, absolute, count = self.GetAccxEff(h2d, cuts)
                    for i in range(1,len(absolute)):
                        ploter_acc_eff.add_hist(absolute[i][1],absolute[i][0])
                    for i in range(len(relative)):
                        ploter_acc_eff_rela.add_hist(relative[i][1],relative[i][0])
                    for i in range(len(count)):
                        ploter_acc_eff_count.add_hist(count[i][1],count[i][0])
                    ploter_acc_eff.plot()
                    ploter_acc_eff_rela.plot()
                    ploter_acc_eff_count.plot()
                    if self.debug: print('AccEff'.ljust(self.cmd_length) + title) 

def task_AN_plots():
    with plots(plot_dir = 'AN_plots') as producer:
        producer.debug_mode(True)
        binning = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70 ,0.80, 0.90, 0.95, 1.00]
        # POI
        producer.add_couplings(cv=1.0,c2v=1.0, c3=20)
        producer.add_couplings(cv=1.0,c2v=20, c3=1.0)
        producer.add_couplings(cv=1.0,c2v=1.0, c3=1.0)

        producer.add_plot_rule(plot_rule([(0,'passMV')],["self.set_topright('Pass m_{V_{jj}}')"]))
        producer.add_plot_rule(plot_rule([(3,'HHSR')],["self.set_topmid('Signal Region')"]))
        producer.add_plot_rule(plot_rule([(3,'SB')],["self.set_topmid('Sideband')"]))

        cuts=[('jetMultiplicity','N_{j}#geq 4'), ('bTags','N_{b}#geq 4'), ('NjOth','N_{j}#geq 6'), ('MV','m_{V}'),('MV_HHSR','SR'),('MV_HHSR_HLT','HLT')]
        producer.AccxEff(cuts)
        # producer.add_hists(['passMV/fourTag/mainView/HHSR/SvB_MA_VHH_ps_BDT_[kVV|kl]'], normalize=True)
        # producer.plot_1d(binning)
        # producer.add_hists(['passMV/fourTag/mainView/HHSR/kl_BDT','passMV/fourTag/mainView/HHSR/[canJets|canVDijets|v4j]/[eta|m_s|m|m_l|phi|pt_m|dR]'], normalize=True)
        # producer.plot_1d()
        producer.add_hists(['passMV/fourTag/mainView/HHSR/m4j_vs_[lead|subl]St_dR'])
        producer.add_hists(['passMV/fourTag/mainView/HHSR/leadSt_m*sublSt_m*'])
        producer.plot_2d()

        producer.no_Data = False
        producer.no_signal = True
        producer.add_hists(['passMV/fourTag/mainView/SB/SvB_MA_VHH_ps_BDT_[kVV|kl]'])
        producer.plot_1d(binning)
        producer.add_hists(['passMV/fourTag/mainView/SB/kl_BDT','passMV/fourTag/mainView/SB/nSelJets','passMV/fourTag/mainView/SB/[canJets|canVDijets|v4j]/[eta|m_s|m|m_l|phi|pt_m|dR]'])
        producer.plot_1d()

def task_ARC_plots():
    with plots(plot_dir = 'ARC_plots') as producer:
        producer.debug_mode(True)
        binning = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70 ,0.80, 0.90, 0.95, 1.00]
        # POI
        producer.no_background = True
        producer.add_couplings(cv=1.0,c2v=1.0, c3=1.0)

        producer.add_plot_rule(plot_rule([(0,'passMV')],["self.set_topright('Pass m_{V_{jj}}')"]))
        producer.add_plot_rule(plot_rule([(3,'HHSR')],["self.set_topmid('Signal Region')"]))
        producer.add_plot_rule(plot_rule([(3,'SB')],["self.set_topmid('Sideband')"]))

        producer.add_hists(['passMV/fourTag/mainView/HHSR/SvB_MA_VHH_ps_BDT_[kVV|kl]'])
        producer.plot_1d(binning)
        producer.add_hists(['passMV/fourTag/mainView/HHSR/kl_BDT','passMV/fourTag/mainView/HHSR/[canJets|canVDijets|v4j]/[eta|m_s|m|m_l|phi|pt_m|dR]'])
        producer.plot_1d()

        producer.no_background = False
        producer.no_Data = False
        producer.no_signal = True
        producer.add_hists(['passMV/fourTag/mainView/SB/SvB_MA_VHH_ps_BDT_[kVV|kl]'])
        producer.plot_1d(binning)
        producer.add_hists(['passMV/fourTag/mainView/SB/kl_BDT','passMV/fourTag/mainView/SB/nSelJets','passMV/fourTag/mainView/SB/[canJets|canVDijets|v4j]/[eta|m_s|m|m_l|phi|pt_m|dR]'])
        producer.plot_1d()

def task_make_datacards(classifier_name, binning):
    with plots() as producer:
        # classifier_name = 'SvB_MA_VHH_ps'
        # binning = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70 ,0.80, 0.90, 0.95, 1.00]
        ONNX = '' #'_ONNX'
        MC_systs = [
            ## b-tagging SF
            # CMS_btag_LF_2016_2017_2018
            systematic([(0,3), (4, '+{}_up_lf')],    'CMS_btag_LF_2016_2017_2018Up'),
            systematic([(0,3), (4, '+{}_down_lf')],  'CMS_btag_LF_2016_2017_2018Down'),
            # CMS_btag_HF_2016_2017_2018
            systematic([(0,3), (4, '+{}_up_hf')],    'CMS_btag_HF_2016_2017_2018Up'),
            systematic([(0,3), (4, '+{}_down_hf')],  'CMS_btag_HF_2016_2017_2018Down'),
            # CMS_btag_hfstats1_2018
            systematic([(0,3), (4, '+{}_up_hfstats1')],    'CMS_btag_hfstats1_{year}Up'),
            systematic([(0,3), (4, '+{}_down_hfstats1')],    'CMS_btag_hfstats1_{year}Down'),
            # CMS_btag_lfstats1_2018
            systematic([(0,3), (4, '+{}_up_lfstats1')],    'CMS_btag_lfstats1_{year}Up'),
            systematic([(0,3), (4, '+{}_down_lfstats1')],    'CMS_btag_lfstats1_{year}Down'),
            # CMS_btag_hfstats2_2018
            systematic([(0,3), (4, '+{}_up_hfstats2')],    'CMS_btag_hfstats2_{year}Up'),
            systematic([(0,3), (4, '+{}_down_hfstats2')],    'CMS_btag_hfstats2_{year}Down'),
            # CMS_btag_lfstats2_2018
            systematic([(0,3), (4, '+{}_up_lfstats2')],    'CMS_btag_lfstats2_{year}Up'),
            systematic([(0,3), (4, '+{}_down_lfstats2')],    'CMS_btag_lfstats2_{year}Down'),
            # CMS_btag_cferr1_2016_2017_2018
            systematic([(0,3), (4, '+{}_up_cferr1')],    'CMS_btag_cferr1_2016_2017_2018Up'),
            systematic([(0,3), (4, '+{}_down_cferr1')],    'CMS_btag_cferr1_2016_2017_2018Down'),
            # CMS_btag_cferr2_2016_2017_2018
            systematic([(0,3), (4, '+{}_up_cferr2')],    'CMS_btag_cferr2_2016_2017_2018Up'),
            systematic([(0,3), (4, '+{}_down_cferr2')],    'CMS_btag_cferr2_2016_2017_2018Down'),
            ## pileup Jet ID SF
            # CMS_eff_j_PUJET_id_2018
            systematic([(0,3), (4, '+{}_up_puId')],    'CMS_eff_j_PUJET_id_{year}Up'),
            systematic([(0,3), (4, '+{}_down_puId')],    'CMS_eff_j_PUJET_id_{year}Down'),
            ## JEC
            # CMS_res_j_2018
            systematic([(0,3), (4, '+{}'+ONNX)],    'CMS_res_j_{year}Up',   'hists_jerUp'),
            systematic([(0,3), (4, '+{}'+ONNX)],    'CMS_res_j_{year}Down', 'hists_jerDown'),
            # CMS_scale_j_2018
            systematic([(0,3), (4, '+{}'+ONNX+'_up_jes')],    'CMS_scale_j_{year}Up',  'hists_jesTotalUp'),
            systematic([(0,3), (4, '+{}'+ONNX+'_down_jes')], 'CMS_scale_j_{year}Down', 'hists_jesTotalDown'),
            ## ZHH NNLO
            # CMS_scale_ZHH_NNLO
            systematic([(0,3), (4, '+{}_up_NNLO')],    'CMS_scale_ZHH_NNLOUp',   'hists', ['VHH', 'ZHH']),
            systematic([(0,3), (4, '+{}_down_NNLO')],    'CMS_scale_ZHH_NNLODown', 'hists', ['VHH', 'ZHH']),
            ## Background
            # CMS_vhh4b_Multijet_FH_basis0
            systematic([(0,3), (4, '+{}_up_bkg_basis0')],    'CMS_vhh4b_Multijet_FH_basis0Up',   'hists', ['multijet_background']),
            systematic([(0,3), (4, '+{}_down_bkg_basis0')],    'CMS_vhh4b_Multijet_FH_basis0Down',   'hists', ['multijet_background']),
            # CMS_vhh4b_Multijet_FH_basis1
            systematic([(0,3), (4, '+{}_up_bkg_basis1')],    'CMS_vhh4b_Multijet_FH_basis1Up',   'hists', ['multijet_background']),
            systematic([(0,3), (4, '+{}_down_bkg_basis1')],    'CMS_vhh4b_Multijet_FH_basis1Down',   'hists', ['multijet_background']),
            # CMS_vhh4b_Multijet_FH_basis2
            systematic([(0,3), (4, '+{}_up_bkg_basis2')],    'CMS_vhh4b_Multijet_FH_basis2Up',   'hists', ['multijet_background']),
            systematic([(0,3), (4, '+{}_down_bkg_basis2')],    'CMS_vhh4b_Multijet_FH_basis2Down',   'hists', ['multijet_background']),
            ## Trigger
            # CMS_vhh4b_TriggerWeight_FH
            systematic([(0,3), (4, '+{}_trigger_up')],    'CMS_vhh4b_TriggerWeight_FHUp'),
            systematic([(0,3), (4, '+{}_trigger_down')],    'CMS_vhh4b_TriggerWeight_FHDown'),
        ]
        # MC_systs = []
        # SR
        producer.save_shape(f'{classifier_name}_'+'shapefile_VhadHH_SR_{year}', 'passMV/fourTag/mainView/HHSR/'+classifier_name, MC_systs, binning, unblind = True)
        producer.save_shape(f'{classifier_name}_'+'shapefile_VhadHH_SR_{year}_kVV', 'passMV/fourTag/mainView/HHSR/'+classifier_name+'_BDT_kVV', MC_systs, binning, unblind = True)
        producer.save_shape(f'{classifier_name}_'+'shapefile_VhadHH_SR_{year}_kl',  'passMV/fourTag/mainView/HHSR/'+classifier_name+'_BDT_kl',  MC_systs, binning, unblind = True)

        # SB
        producer.save_shape(f'{classifier_name}_'+'shapefile_VhadHH_SB_{year}', 'passMV/fourTag/mainView/SB/'+classifier_name, MC_systs, binning, unblind = True)
        producer.save_shape(f'{classifier_name}_'+'shapefile_VhadHH_SB_{year}_kVV', 'passMV/fourTag/mainView/SB/'+classifier_name+'_BDT_kVV', MC_systs, binning, unblind = True)
        producer.save_shape(f'{classifier_name}_'+'shapefile_VhadHH_SB_{year}_kl',  'passMV/fourTag/mainView/SB/'+classifier_name+'_BDT_kl', MC_systs, binning, unblind = True)

        # # Mix
        # for i in range(1):
        #     mix_n = str(i)
        #     producer.save_shape('shapefile_VhadHH_Mix_{year}_kl',  'passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps_BDT_kl',  MC_systs, binning, mix_as_obs = 'ZZ4b/nTupleAnalysis/combine/hists_VHH_closure_3bDvTMix4bDvT_HHSR_weights_newSBDef.root:3bDvTMix4bDvT_v'+mix_n+'/VHH_ps_lbdt{year}')
        #     producer.save_shape('shapefile_VhadHH_Mix_{year}_kVV', 'passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps_BDT_kVV', MC_systs, binning, mix_as_obs = 'ZZ4b/nTupleAnalysis/combine/hists_VHH_closure_3bDvTMix4bDvT_HHSR_weights_newSBDef.root:3bDvTMix4bDvT_v'+mix_n+'/VHH_ps_sbdt{year}')

def task_make_gif():
    with plots() as producer:
        producer.debug_mode(True)
        producer.add_plot_rule(plot_rule([(0,'passMV'),(3,'HHSR')],["self.set_topright('HHSR Pass m_{V_{jj}}')"]))
        producer.add_plot_rule(plot_rule([], ["self.set_topmid(self.title)"]))

        producer.add_couplings(cv=1.0,c2v=1.0, c3=list(np.arange(-3,5,0.1)))
        producer.add_hists(['passMV/fourTag/mainView/HHSR/v4j/[eta|m_l|pt_m]'])
        producer.plot_1d_animation(tag='c3_scan')

        producer.add_couplings(cv=1.0,c2v=list(np.arange(-5,5,0.1)), c3=1.0)
        producer.add_hists(['passMV/fourTag/mainView/HHSR/v4j/[eta|m_l|pt_m]'])
        producer.plot_1d_animation(tag='c2v_scan')

def task_make_eff_unified():
    with plots() as producer:
        producer.mc_signals = True
        producer.debug_mode(True)
        producer.add_hists(['passMV/fourTag/mainView/HHSR/gen_*HH*'])
        producer.save('FH_eff_numerator', 5)

class hist_info:
    def __init__(self, root, hist , data = None, scale = None):
        self.hist  = hist
        self.root  = root
        self.data  = data
        self.scale = scale
    def get(self, rebin):
        if self.data is None:
            _root_file = ROOT.TFile(self.root, 'READ')
            _hist      = _root_file.Get(self.hist)
            _hist.SetDirectory(0)
            self.data = _hist
            _root_file.Close()
            if self.scale:
                self.data.Scale(self.scale)
        return rebin_hist(self.data, rebin)


class histogram_1d_customize:
    def __init__(self, path, title = '', tag = '', normalize = False, x_label = '', y_label = '', rules = [], event_count = False):
        self.path = path
        self.title = title
        self.tag = tag
        self.normalize = normalize
        self.rules = rules
        self.event_count = event_count

        self.curves = {}
        self.stacks = {}
        self.stack_sum = {}
        self.error  = {}
        self.ratios = []

        self.legends = []
        self.lines = 0

        self.x_max = float('-inf')
        self.x_min = float('inf')
        self.x_label = x_label
        self.y_max = float('-inf')
        self.y_min = 0
        self.y_label = y_label
        self.topmid_label = ''
        self.topright_label = ''

    def set_topright(self, label):
        self.topright_label = label

    def set_topmid(self, label):
        self.topmid_label = label

    def add_stack(self, hists, stack_tag, scale = 1.0):
        stack = ROOT.THStack()
        colors = [ROOT.kAzure-9, ROOT.kYellow, ROOT.kRed-4, ROOT.kGreen+1, ROOT.kViolet-7, ROOT.kMagenta-9]
        sum = None
        for i, tag in enumerate(hists.keys()):
            hist = hists[tag]
            total, error = integral_error(hist)
            if total == 0.0:
                continue
            if sum is None:
                sum = hist.Clone()
            else:
                sum.Add(hist)
            hist.SetFillColor(colors[i])
            stack.Add(hist)
            option = 'f'
            label, lines = self.set_count(tag + ('' if scale == 1 or self.normalize else ' (#times' + str(scale) + ')'), total, error)
            self.lines += lines
            self.legends.append((hist, label, option))
            x_axis = hist.GetXaxis()
            self.x_max = max(x_axis.GetXmax(), self.x_max)
            self.x_min = min(x_axis.GetXmin(), self.x_min)
            if self.x_label == '': self.x_label = x_axis.GetTitle()
        self.y_max = max(stack.GetMaximum(), self.y_max)
        self.y_min = min(stack.GetMinimum(), self.y_min)
        self.stacks[stack_tag] = stack
        self.stack_sum[stack_tag] = sum
        hist_error = sum.Clone()
        hist_error.SetFillStyle(3125)
        hist_error.SetFillColor(ROOT.kGray + 2)
        hist_error.SetMarkerSize(0)
        self.error[stack_tag]= hist_error
    
    def add_hist(self, hist, tag, scale = 1.0):
        total, error = integral_error(hist)
        if total == 0.0:
            return
        colors = [ROOT.kBlack, ROOT.kRed-4, ROOT.kGreen+1, ROOT.kViolet-7, ROOT.kMagenta-9]
        hist.Scale(scale)
        hist.SetLineColor(colors[len(self.curves)])
        hist.SetMarkerColor(colors[len(self.curves)])
        hist.SetMarkerSize(1)
        hist.SetMarkerStyle(8)   
        x_axis = hist.GetXaxis()
        y_axis = hist.GetYaxis()
        self.x_max = max(x_axis.GetXmax(), self.x_max)
        self.x_min = min(x_axis.GetXmin(), self.x_min)
        self.y_max = max(hist.GetMaximum(), self.y_max)
        self.y_min = min(hist.GetMinimum(), self.y_min)
        if self.x_label == '': self.x_label = x_axis.GetTitle()
        if self.y_label == '': self.y_label = y_axis.GetTitle()

        option = 'l pe'
        self.curves[tag] = hist

        hist_error = hist.Clone()
        hist_error.SetFillStyle(3125)
        hist_error.SetFillColor(ROOT.kGray + 2)
        hist_error.SetMarkerSize(0)
        self.error[tag]= hist_error

        label, lines = self.set_count(tag + ('' if scale == 1 or self.normalize else ' (#times' + str(scale) + ')'), total, error)
        self.lines += lines
        self.legends.append((hist, label, option))

    def set_font(self, text, num = 42):
        return '#font[' + str(num) + ']{' + text + '}'
    
    def set_count(self, label, count = 0, error = 0):
        if self.event_count and count != 0 and error != 0:
            return '#splitline{' + label + '}{' + '{:.2f}'.format(count) + ' #pm ' + '{:.2f}'.format(error) + '}', 2
        else:
            return label, 1

    def plot(self, options = ''):
        allow_ratio = ('Data' in self.curves)

        legend_height = (0.04 if allow_ratio else 0.05) * self.lines
        self.legend = ROOT.TLegend(0.0, max(0.0, 0.95 - legend_height), 1.0, 0.95)
        self.legend.SetTextSize(0.06)
        self.legend.SetTextFont(42)
        self.legend.SetBorderSize(0)
        for legend in self.legends:
            self.legend.AddEntry(legend[0], legend[1], legend[2])

        for rule in self.rules:
            rule.apply(self)
        canvas_gen = canvas_helper.ROOTCanvas(self.x_min, self.x_max, self.y_min, self.y_max * 1.05)
        canvas_gen.TopMid.Text = self.set_font(self.topmid_label)
        canvas_gen.TopRight.Text = self.set_font(self.topright_label)
        canvas_gen.XLabel.Text = self.set_font(self.x_label)
        canvas_gen.YLabel.Text = self.set_font(self.y_label)
        canvas_gen.AllowLegend = True
        canvas_gen.AllowRatio  = allow_ratio
        canvas = canvas_gen.GetCanvas(self.title)
        canvas_gen.MainPad.cd()
        for stack in self.stacks.keys():
            self.stacks[stack].Draw('SAME HIST ' + options)
            self.error[stack].Draw('SAME E2')

        for tag in self.curves.keys():
            self.curves[tag].Draw('SAME P E' + options)

        canvas_gen.Legend.cd()
        self.legend.Draw()
        if allow_ratio:
            colors = [ROOT.kBlack, ROOT.kRed-4, ROOT.kGreen+1, ROOT.kViolet-7, ROOT.kMagenta-9]
            ratio_range = 0.5
            total = 0
            canvas_gen.Ratio.cd()
            frame = canvas_gen.Ratio.DrawFrame(self.x_min, 1.0 - ratio_range, self.x_max, 1.0 + ratio_range)
            y_axis = frame.GetYaxis()
            y_axis.SetLabelSize(0.14)
            y_axis.SetNdivisions(2, 5, 0, False)
            x_axis = frame.GetXaxis()
            x_axis.SetLabelSize(0)
            canvas_gen.Ratio.SetGridy()
            label=ROOT.TLatex()
            label.SetTextSize(0.16)
            label.SetTextAngle(90)
            label.SetTextAlign(21)

            ratio_legend_height = (0.04 if allow_ratio else 0.05) * (len(self.stack_sum) + len(self.curves) - 1)
            self.ratio_legend = ROOT.TLegend(0.0, 0.05, 1.0, 0.05 + ratio_legend_height)
            self.ratio_legend.SetTextSize(0.06)
            self.ratio_legend.SetTextFont(42)
            self.ratio_legend.SetBorderSize(0)
            for tag in self.stack_sum.keys() + self.curves.keys():
                if tag == 'Data':
                    continue
                if tag in self.stack_sum:
                    hist = self.stack_sum[tag]
                else:
                    hist = self.curves[tag]
                if hist is None:
                    continue
                ratio = self.curves['Data'].Clone()
                ratio.Divide(hist)
                ratio.SetLineColor(colors[total])
                ratio.SetMarkerColor(colors[total])
                ratio.SetMarkerSize(1)
                ratio.SetMarkerStyle(8) 
                self.ratios.append(ratio)
                ratio.Draw('SAME X0 P E1')
                total += 1
                self.ratio_legend.AddEntry(ratio, 'Data/'+tag, 'X0 P E1')
            canvas_gen.Ratio.RedrawAxis()
            canvas_gen.Legend.cd()
            self.ratio_legend.Draw()
        canvas_gen.MainPad.RedrawAxis()
        canvas.Print(self.path + self.tag + PLOT_FORMAT)

    def apply(self, action):
        exec(action)

def compare_standalone(hists, rebin, path, rules, normalize = False):
    plotter = histogram_1d_customize(path, title = '', tag = '', normalize = False, x_label = '', y_label = '', rules = rules, event_count = True)
    for hist in hists.keys():
        if isinstance(hists[hist], dict):
            stack = {}
            for tag in hists[hist].keys():
                stack[tag] = hists[hist][tag].get(rebin)
            plotter.add_stack(stack, hist)
        else:
            plotter.add_hist(hists[hist].get(rebin), hist)
    plotter.plot()

def task_compare_mix_data(add_jcm = False):
    n_mix = 15
    classifier_name = 'SvB_MA_VHH'
    binning = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70 ,0.80, 0.90, 0.95, 1.00]
    
    MIX_PATH = '/uscms/home/'+USER+'/nobackup/CMSSW_11_1_0_pre5/src/ZZ4b/nTupleAnalysis/combine/hists_VHH_closure_3bDvTMix4bDvT_HHSR_weights_newSBDef.root'
    COMPARE_HIST = 'passMV/{nTag}Tag/mainView/HHSR/'+classifier_name+'_ps{cat}'
    CAT_MIX = {'_BDT_kl':'_lbdt', '_BDT_kVV':'_sbdt', '':''}

    output_dir = 'compares/'

    if not os.path.isdir(HIST_PATH + output_dir):
        os.mkdir(HIST_PATH + output_dir)

    MIX_AVG = {}

    for cat in CAT_MIX.keys():
        MIX_AVG[cat]={}
        for year in ['2016', '2017', '2018', 'RunII']:
            MIX_AVG[cat][year] = None
            for mix in ['3bDvTMix4bDvT_v'+str(i)+'/VHH_ps{cat}{year}/data_obs' for i in range(n_mix)]:
                mix_hist_info = hist_info(MIX_PATH, mix.format(cat = CAT_MIX[cat], year = year))
                if MIX_AVG[cat][year] is None:
                    MIX_AVG[cat][year] = mix_hist_info.get(1)
                else:
                    MIX_AVG[cat][year].Add(mix_hist_info.get(1))
            MIX_AVG[cat][year].Scale(1.0/n_mix)

    MULTIJETS_JCM = {}
    if add_jcm:
        for cat in CAT_MIX.keys():
            MULTIJETS_JCM[cat]={}
            for year in ['2016', '2017', '2018', 'RunII']:
                multijet_file = hist_info(HIST_PATH + 'data'+ year + '_3b/hists_j.root', COMPARE_HIST.format(nTag = 'three', cat = cat))
                ttbar_file = hist_info(HIST_PATH + 'TT'+ year + '_3b/hists_j.root', COMPARE_HIST.format(nTag = 'three', cat = cat))
                MULTIJETS_JCM[cat][year] = multijet_file.get(1)
                MULTIJETS_JCM[cat][year].Add(ttbar_file.get(1), -1.0)

    for mix in [['3bDvTMix4bDvT_v'+str(i)+'/VHH_ps{cat}{year}/data_obs', 'mix'+str(i), None] for i in range(n_mix)] + [['', 'mix_avg', MIX_AVG]]:
        output_path = HIST_PATH + output_dir+mix[1]+'/'
        if not os.path.isdir(output_path):
            os.mkdir(output_path)
        for jcm in [False] + ([True] if add_jcm else []):
            for cat in CAT_MIX.keys():
                for year in ['2016', '2017', '2018', 'RunII']:
                    compare_standalone(
                    hists = {'Data':hist_info(HIST_PATH + 'data'+ year + '_4b/hists_j'+('' if jcm else '_r')+'.root', COMPARE_HIST.format(nTag = 'four', cat = cat)), 
                    'Mix Data':hist_info(MIX_PATH, mix[0].format(cat = CAT_MIX[cat], year = year), mix[2][cat][year] if mix[2] is not None else mix[2]), 
                    'Background':{'Multijet'+('(JCM)' if jcm else ''):hist_info(HIST_PATH + 'data'+ year + '_3b/hists_j'+('' if jcm else '_r')+'.root', COMPARE_HIST.format(nTag = 'three', cat = cat), MULTIJETS_JCM[cat][year] if jcm else None),
                    'TTbar':hist_info(HIST_PATH + 'TT'+ year + '_4b/hists_j'+('' if jcm else '_r')+'.root', COMPARE_HIST.format(nTag = 'four', cat = cat))}},
                    rebin = binning,
                    path  = output_path+('JCM' if jcm else '')+year+cat+'_'+mix[1],
                    rules = [plot_rule([],["self.set_topright('Pass m_{V_{jj}}')"]), plot_rule([],["self.set_topmid('"+year+" Signal Region')"])],
                )
    os.system('tar -C ' + HIST_PATH + ' -cvf  ' + HIST_PATH + 'compares.tar.gz compares/')
    
if __name__ == '__main__':
    task_make_datacards('card_mHH', [0, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850])
    task_make_datacards('card_V_pT', [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640])
    task_make_datacards('card_mH1_mH2', [-100, -70, -60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 100])

    # task_ARC_plots()
    # task_make_datacards()
    # task_make_gif()
    # task_compare_mix_data()
    # task_make_eff_unified()

    # with plots(plot_dir = 'AN_plots') as producer:
    #     producer.debug_mode(True)
    #     binning = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70 ,0.80, 0.90, 0.95, 1.00]
    #     # POI
    #     producer.add_couplings(cv=1.0,c2v=1.0, c3=20)
    #     producer.add_couplings(cv=1.0,c2v=20, c3=1.0)
    #     producer.add_couplings(cv=1.0,c2v=1.0, c3=1.0)

    #     producer.add_plot_rule(plot_rule([(0,'passPreSel')],["self.set_topright('Pass Pre-selection')"]))
    #     producer.add_plot_rule(plot_rule([(0,'passNjOth')],["self.set_topright('Pass N_{j}#geq 6')"]))
    #     producer.add_plot_rule(plot_rule([(0,'passMV')],["self.set_topright('Pass m_{V_{jj}}')"]))
    #     producer.add_plot_rule(plot_rule([(3,'HHSR')],["self.set_topmid('Signal Region')"]))
    #     producer.add_plot_rule(plot_rule([(3,'SB')],["self.set_topmid('Sideband')"]))

    #     producer.no_Data = False
    #     producer.no_signal = True
    #     producer.plot_1d(binning)
    #     producer.add_hists(['pass*/fourTag/mainView/SB/kl_BDT','pass*/fourTag/mainView/SB/[*Jets|*Dijets|v4j]/[eta|m*|phi|pt*|dR]', 'pass*/fourTag/mainView/SB/n*','pass*/fourTag/mainView/SB/SvB_MA_VHH_ps_BDT_[kVV|kl]'])

    #     producer.add_hists(['passMV/fourTag/mainView/HHSR/kl_BDT','passMV/fourTag/mainView/HHSR/[*Jets|*Dijets|v4j]/[eta|m*|phi|pt*|dR]', 'passMV/fourTag/mainView/HHSR/n*','passMV/fourTag/mainView/HHSR/SvB_MA_VHH_ps_BDT_[kVV|kl]'])
    #     producer.plot_1d()
    # ...
