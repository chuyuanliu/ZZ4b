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
in_path = '/uscms/home/'+USER+'/nobackup/VHH/'
out_path = in_path + 'plots/'
years = ['RunII', '2016', '2017', '2018']
# signals = ['VHH', 'ZHH', 'WHH']
# years = ['2016', '2017', '2018']
# signals = ['ZHH', 'WHH']
# years = ['RunII']
signals = ['VHH']
hists_filename = {
    'data'    : ['hists_j_r'],
    'ttbar'   : ['hists_j_r'],
    'signal'  : ['hists', 'hists_jerUp', 'hists_jerDown', 'hists_jesTotalUp', 'hists_jesTotalDown'],
    # 'signal'  : ['hists'],
    # 'data'    : ['hists_j_r', 'hists_j_r_14', 'hists_j_r_14n', 'hists_j_r_14nc', 'hists_j_r_8', 'hists_j_r_8n', 'hists_j_r_8nc'],
    # 'ttbar'   : ['hists_j_r', 'hists_j_r_14', 'hists_j_r_14n', 'hists_j_r_14nc', 'hists_j_r_8', 'hists_j_r_8n', 'hists_j_r_8nc'],
    # 'signal'  : ['hists', 'hists_14', 'hists_14n', 'hists_14nc', 'hists_8', 'hists_8n', 'hists_8nc'],
}
no_background = False
no_multijet = False
no_signal = False
mc_only = False
mc_signals = False
event_count = True
signal_scale = 1
use_density = False

if not os.path.isdir(out_path):
    os.mkdir(out_path)

# General

def integral(hist):
    n_bins = hist.GetNbinsX()
    total = hist.Integral(0, n_bins + 1)
    return total

def integral_error(hist):
    n_bins = hist.GetNbinsX()
    error = ROOT.Double()
    total = hist.IntegralAndError(0, n_bins + 1, error)
    return total, float(error)

def round_up(value, base):
    return int(value/base) * base + base

def get_ratio_range(max):
    diff = abs(1 - max)
    if diff < 0.05:
        return round_up(diff, 0.01)
    else:
        return round_up(diff, 0.05)


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
    def __init__(self, path, title = '', tag = '', normalize = False, x_label = '', y_label = '', y_range = None, smooth = False, rules = []):
        self.path = path
        self.title = title
        self.tag = tag
        self.normalize = normalize
        self.rules = rules

        self.signals = {}
        self.data = None
        self.ttbar = None
        self.multijet = None
        self.background = ROOT.THStack()

        self.legends = []
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

        if total == 0.0:
            return
        if self.normalize and 't#bar{t}' not in tag and 'Multijet' not in tag:
            scale = 1.0 / total
        
        hist.Scale(scale)
        hist.SetLineColor(line_color)
        x_axis = hist.GetXaxis()
        y_axis = hist.GetYaxis()
        self.x_max = max(x_axis.GetXmax(), self.x_max)
        self.x_min = min(x_axis.GetXmin(), self.x_min)
        if not (self.normalize and ('t#bar{t}' in tag or 'Multijet' in tag)):
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
        else:
            self.signals[tag] = hist

        label, lines = self.set_count(tag + ('' if scale == 1 or self.normalize else ' (#times' + str(scale) + ')'), total, error)
        self.lines += lines
        self.legends.append((hist, label, option))

    def set_font(self, text, num = 42):
        return '#font[' + str(num) + ']{' + text + '}'
    
    def set_count(self, label, count = 0, error = 0):
        if event_count and count != 0 and error != 0 and not self.smooth:
            return '#splitline{' + label + '}{' + '{:.2f}'.format(count) + ' #pm ' + '{:.2f}'.format(error) + '}', 2
        else:
            return label, 1

    def plot(self, options = ''):
        background_scale = 1.0
        if self.normalize:
            total = 0.0
            if self.ttbar is not None:
                n_bins = self.ttbar.GetNbinsX()
                total += integral(self.ttbar)
            if self.multijet is not None:
                n_bins = self.multijet.GetNbinsX()
                total += integral(self.multijet)
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
        if self.data is not None:
            self.data.SetMarkerColor(ROOT.kBlack)
            self.data.SetMarkerSize(1)
            self.data.SetMarkerStyle(8)   

        allow_ratio = (self.multijet is not None) and (self.ttbar is not None) and (self.data is not None) # TEMP     

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
        canvas_gen.AllowLegend = True
        canvas_gen.AllowRatio  = allow_ratio
        canvas = canvas_gen.GetCanvas(self.title)
        canvas_gen.MainPad.cd()
        self.background.Draw('SAME HIST ' + options)
        if self.data is not None:
            self.data.Draw('SAME P E ' + options)
        temp = {} # TEMP
        for signal in self.signals:
            if self.smooth:
                self.legend.SetTextSize(0.08) # TEMP
                self.signals[signal].Draw('SAME HIST PLC C') # TEMP
                temp[signal] = self.signals[signal].Clone() # TEMP
                temp[signal].SetMarkerSize(1) # TEMP
                temp[signal].SetMarkerStyle(8) # TEMP
                temp[signal].Draw('SAME X0 E1') # TEMP
            else:
                self.signals[signal].Draw('SAME HIST PLC ' + options)
        canvas_gen.Legend.cd()
        self.legend.Draw()
        if allow_ratio: # TEMP
            ratio_range = 0.1
            ratio = self.data.Clone()
            bkgd = self.ttbar.Clone()
            bkgd.Add(self.multijet)
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
        canvas.Print(self.path + self.tag + '.pdf')

    def apply(self, action):
        exec(action)

class histogram_1d_syst:
    def __init__(self, path, title, tag = '', x_label = '', y_label = '', rules = []):
        self.path = path
        self.title = title
        self.tag = tag
        self.rules = rules

        self.systs = {} # central, up, down

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

    def plot(self):
        for rule in self.rules:
            rule.apply(self)
        for tag in self.systs:
            canvas_gen = canvas_helper.ROOTCanvas(self.x_min[tag], self.x_max[tag], self.y_min[tag], self.y_max[tag] * 1.05)
            canvas_gen.TopMid.Text = self.set_font(self.topmid_label)
            canvas_gen.TopRight.Text = self.set_font(self.topright_label)
            canvas_gen.XLabel.Text = self.set_font(self.x_label)
            canvas_gen.YLabel.Text = self.set_font(self.y_label)
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
            label.DrawLatex(canvas_gen.Var.GetX(-0.08), 1.0, self.set_font('Up(Down)/Central'))
            central_error.Draw('SAME E2')
            for shift in ['up', 'down']:
                ratio[shift].Draw('SAME X0 P E1')
            canvas.Print(self.path + tag + self.tag + '.pdf')

       
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
            self.hists[tag].Draw(options)
            for curve in self.curves:
                curve.Draw('SAME')
            canvas.RedrawAxis()
            canvas.Print(self.path + tag + self.tag + '.pdf')

class datacard:
    def __init__(self, path, shape_file, datacard_file):
        pass
class systematic:
    def __init__(self, pattern = '', name = '', filename = None, signal = None):
        self.pattern  = pattern
        self.name     = name
        self.filename = filename
        self.signal   = signal
    def check_signal(self, signal):
        if self.signal is None: return True
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
    def __init__(self, basis = [{},{'cv':0.5},{'cv':1.5},{'c2v':0.0},{'c2v':2.0},{'c3':0.0},{'c3':2.0},{'c3':20.0}], match_all_dirs = True, ignore_case = True, debug = False, cmd_length =20):
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

        self.input = in_path
        self.output = out_path
        self.years = years
        self.signals = signals

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

        self.data_filename = hists_filename['data']
        self.ttbar_filename = hists_filename['ttbar']
        self.signal_filename = hists_filename['signal']

        self.plot_rules = []
        self.couplings = coupling_weight_generator(basis = basis, debug = self.debug, cmd_length = self.cmd_length)
        self.match = wildcard_match(match_all_dirs, ignore_case, debug = self.debug, cmd_length = self.cmd_length)
        self.base_path = path_extensions(self.output, clean = True, debug = self.debug, cmd_length = self.cmd_length)

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

        for year in self.years:
            for filename in self.data_filename:
                self.data_files_4b[year][filename] = ROOT.TFile(self.input + 'data' + year + '_4b/' + filename + '.root', 'READ')
                self.data_files_3b[year][filename] = ROOT.TFile(self.input + 'data' + year + '_3b/' + filename + '.root', 'READ')
            for filename in self.ttbar_filename:
                self.ttbar_files_4b[year][filename] = ROOT.TFile(self.input + 'TT' + year + '_4b/' + filename + '.root', 'READ')
                self.ttbar_files_3b[year][filename] = ROOT.TFile(self.input + 'TT' + year + '_3b/' + filename + '.root', 'READ')
            for filename in self.signal_filename:
                for signal in self.signals:
                    for coupling in self.couplings.get_all_filenames():
                        root_path = self.input + signal + 'To4B' + coupling + year + '/' + filename + '.root'
                        if os.path.isfile(root_path):
                            self.signal_files[year][signal][filename].append(ROOT.TFile(root_path, 'READ'))
                        else:
                            print('Error'.ljust(self.cmd_length) + 'file not found ' + root_path)
                            self.signal_files[year][signal][filename].append(None)
        self.root_dir = self.signal_files[self.years[0]][self.signals[0]][self.signal_filename[0]][0].GetDirectory('')
        if no_signal:
            self.root_dir = self.ttbar_files_3b[self.years[0]].GetDirectory('')
        self.modify_plot_hists_list_recursive('', self.initialize_hist)

        # TODO add intelligent color
        # TODO add html viewer
        # TODO rewrite add/remove logic (async)
        # TODO RAM management

    def __enter__(self):
        return self

    def __exit__(self, *args):
        os.system('tar -C ' + self.input + ' -cvf ' + self.input + 'plots.tar.gz plots/')
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

    def rebin(self, hist, rebin_x, rebin_y = None):
        if hist.GetSumw2N() == 0: hist.Sumw2()
        if rebin_y is None:
            rebin_y = rebin_x
        if isinstance(rebin_x, list):
            nbins = len(rebin_x) - 1
            bins = array.array('d', rebin_x)
            new_hist = hist.Rebin(nbins, hist.GetTitle()+'_rebinned', bins)
            if use_density:
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

    def load_signal_mc_hists(self, year, signal, hist, rebin_x = 1, rebin_y = None, filename = None):
        hists = []
        if filename is None:
            filename = self.signal_filename[0]
        for file in self.signal_files[year][signal][filename]:
            if file is None:
                return None
            else:
                signal = self.rebin(file.Get(hist), rebin_x, rebin_y)
                hists.append(signal)
        return hists

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
        ttbar = self.rebin(self.ttbar_files_4b[year][filename].Get(hist), rebin_x, rebin_y)
        return ttbar
    
    def load_ttbar_3b_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if filename is None:
            filename = self.ttbar_filename[0]
        if self.ttbar_files_3b[year][filename] is None:
            return None
        ttbar = self.rebin(self.ttbar_files_3b[year][filename].Get(hist), rebin_x, rebin_y)
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
        data = self.rebin(self.data_files_4b[year][filename].Get(hist), rebin_x, rebin_y)
        return data

    def load_data_3b_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if filename is None:
            filename = self.data_filename[0]
        if self.data_files_3b[year][filename] is None:
            return None
        data = self.rebin(self.data_files_3b[year][filename].Get(hist), rebin_x, rebin_y)
        return data

    def load_multijet_hists(self, year, hist, rebin_x = 1, rebin_y = None, filename = None):
        if filename is None:
            filename = self.data_filename[0]
        if self.data_files_3b[year][filename] is None:
            return None
        path = copy(self.all_hists[hist])
        path[1] = 'threeTag'
        path = self.join_hist_path(path)
        if self.data_filename == 'hists_j':
            hist_multijet = self.data_files_3b[year][filename].Get(path).Clone()
            if hist_multijet.GetSumw2N() == 0: hist.Sumw2()
            hist_ttbar = self.ttbar_files_4b[year][filename].Get(path).Clone()
            if hist_ttbar.GetSumw2N() == 0: hist.Sumw2()
            hist_multijet.Add(hist_ttbar, -1)
            hist_multijet = self.rebin(hist_multijet, rebin_x, rebin_y)
            return hist_multijet
        else:
            multijet = self.rebin(self.data_files_3b[year][filename].Get(path), rebin_x, rebin_y)
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
        self.couplings.debug = debug
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

    def add_couplings(self, cv = 1.0, c2v = 1.0, c3 = 1.0):
        if not isinstance(cv, list): cv = [cv]
        if not isinstance(c2v, list): c2v = [c2v]
        if not isinstance(c3, list): c3 = [c3]
        for cv_iter in cv:
            for c2v_iter in c2v:
                for c3_iter in c3:
                    self.plot_couplings.append({'cv':cv_iter, 'c2v':c2v_iter, 'c3':c3_iter})
    def add_plot_rule(self, rule):
        self.plot_rules.append(rule)

    def plot_1d(self, rebin = 1, options = ''): #TEMP
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
                    ploter = histogram_1d_collection(path, title=hist, normalize = self.plot_hists[hist],y_label='Events',rules=rules)
                    if not no_background and not mc_only:
                        ploter.add_hist(self.load_data_hists(year, hist, rebin), 'Data ' + self.lumi[year] + ' ' + year)
                        if not no_multijet:
                            ploter.add_hist(self.load_multijet_hists(year, hist, rebin), 'Multijet Model')
                    if not no_background:
                        ploter.add_hist(self.load_ttbar_mc_hists(year, hist, rebin), 't#bar{t}')
                    if not no_signal:
                        signal_mc = self.load_signal_mc_hists(year, signal, hist, rebin)
                    else:
                        signal_mc = None
                    if signal_mc is not None:
                        if mc_signals: 
                            for i,coupling in enumerate(self.couplings.basis):
                                ploter.add_hist(signal_mc[i], self.couplings.get_caption(**coupling), signal_scale)
                        else:
                            for coupling in self.plot_couplings:
                                weights = self.couplings.generate_weight(**coupling)
                                ploter.add_hist(self.sum_hists(signal_mc, weights), self.couplings.get_caption(**coupling), signal_scale)
                    ploter.plot(options)

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
                    if mc_signals: 
                        for i,coupling in enumerate(self.couplings.basis):
                            couplingName = self.couplings.get_filename(**coupling)[1:-1]
                            ploter = histogram_1d_collection(path + couplingName, title=hist, normalize = normalize, y_label='Events', rules=rules)
                            for file in histFiles_sig.keys():
                                ploter.add_hist(signal_mc[file][i], histFiles_sig[file])
                            ploter.plot()
                    else:
                        for coupling in self.plot_couplings:
                            couplingName = self.couplings.get_filename(**coupling)[1:-1]
                            ploter = histogram_1d_collection(path + couplingName, title=hist, normalize = normalize, y_label='Events', rules=rules)
                            weights = self.couplings.generate_weight(**coupling)
                            for file in histFiles_sig.keys():
                                ploter.add_hist(self.sum_hists(signal_mc[file], weights), histFiles_sig[file])
                            ploter.plot()
                    ploter = histogram_1d_collection(path + 'ttbar', title=hist, normalize = normalize, y_label='Events', rules=rules)
                    for file in histFiles_bkg.keys():
                        ploter.add_hist(ttbar_mc[file], histFiles_bkg[file])
                    ploter.plot()
                    ploter = histogram_1d_collection(path + 'multijet', title=hist, normalize = normalize, y_label='Events', rules=rules)
                    for file in histFiles_bkg.keys():
                        ploter.add_hist(multijet[file], histFiles_bkg[file])
                    ploter.plot()

    def plot_syst(self, pattern, systs, tag = '', rebin = 1):
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
                    ploter = histogram_1d_syst(path, title=hist,rules=rules)           
                    if mc_signals: 
                        for i,coupling in enumerate(self.couplings.basis):
                            signals = {}
                            for syst in systs:
                                signals[syst] = signal_mc[syst][i]
                            ploter.add_hist(signals, self.couplings.get_filename(**coupling)[1:-1])
                    else:
                        for coupling in self.plot_couplings:
                            signals = {}
                            weights = self.couplings.generate_weight(**coupling)
                            for syst in systs:
                                signals[syst] = self.sum_hists(signal_mc[syst], weights)
                            ploter.add_hist(signals, self.couplings.get_filename(**coupling)[1:-1])
                    ploter.plot()

    def plot_2d(self, options = 'COLZ'): #TEMP
        for year in self.years:
            for signal in self.signals:
                for hist in self.plot_hists:
                    if self.debug: print('Plot'.ljust(self.cmd_length) + hist) 
                    if not isinstance(signal_mc[0], ROOT.TH2):
                        continue
                    path = self.path[year][signal].mkdir(self.all_hists[hist])
                    ploter = histogram_2d_collection(path, title=hist)
                    if not no_background:
                        ploter.add_hist(self.load_data_hists(year, hist), 'Data')
                        ploter.add_hist(self.load_ttbar_mc_hists(year, hist), 'TTbar')
                        if not no_multijet:
                            ploter.add_hist(self.load_multijet_hists(year, hist), 'Multijet')
                    if not no_signal:
                        signal_mc = self.load_signal_mc_hists(year, signal, hist)
                    else:
                        signal_mc = None
                    if signal_mc is not None:
                        if mc_signals: 
                            for i,coupling in enumerate(self.couplings.basis):
                                ploter.add_hist(signal_mc[i], self.couplings.get_filename(**coupling)[1:-1])
                        else:
                            for coupling in self.plot_couplings:
                                weights = self.couplings.generate_weight(**coupling)
                                ploter.add_hist(self.sum_hists(signal_mc, weights), self.couplings.get_filename(**coupling)[1:-1])
                    if 'm4j' in hist and 'leadSt_dR' in hist:
                        ploter.add_curve('650.0/x+0.5', range=[None, 650])
                        ploter.add_curve('360.0/x-0.5')
                        ploter.add_curve('1.5', range = [650, None])
                        ploter.add_curve('840.0/x-0.1',range = [None, 525], color=ROOT.kGreen+2)
                        ploter.add_curve('1.5',range = [525, None], color=ROOT.kGreen+2)
                        ploter.add_curve('250.0/x-0.5',color=ROOT.kGreen+2)
                    if 'm4j' in hist and 'sublSt_dR' in hist:
                        ploter.add_curve('650.0/x+0.7', range=[None, 812.5])
                        ploter.add_curve('235.0/x')
                        ploter.add_curve('1.5', range=[812.5, None])
                    if 'm6j' in hist and 'V_dR' in hist:
                        ploter.add_curve('650.0/x+0.3', range=[None, 650], color=ROOT.kGreen+2)
                        ploter.add_curve('1.3', range=[650, None], color=ROOT.kGreen+2)
                    if 'leadSt_m' in hist and 'sublSt_m' in hist:
                        ploter.add_curve('(((x-125*1.02)/(0.1*x))**2+((y-125*0.98)/(0.1*y))**2)',[1.9**2])
                        ploter.add_curve('(((x+y-245)/1.2)**2+(x-y-5)**2)',[2*22**2], color=ROOT.kGreen+2)
                    ploter.plot(options)

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
    
    def save(self, path):
        save_path = path_extensions(self.output + path, clean = True, debug = self.debug, cmd_length = self.cmd_length)
        


    def save_shape(self, filename, hist, MC_systs = [], rebin = 1, unblind = False, mix_as_obs = ''):
        for year in self.years:
            format_args = {'year': year}
            output_file = ROOT.TFile(self.input + filename.format(**format_args) + '.root','recreate')                
            output_file.cd()
            multijet = self.load_multijet_hists(year, hist, rebin)
            multijet.SetNameTitle('multijet_background','multijet_background_'+year)
            ttbar = self.load_ttbar_mc_hists(year, hist, rebin)
            ttbar.SetNameTitle('ttbar_background','ttbar_background'+year)
            multijet.Write()
            ttbar.Write()
            x_axis = ttbar.GetXaxis()
            if unblind:
                data = self.load_data_4b_hists(year, hist, rebin)
                data.SetNameTitle('data_obs', 'data_obs_'+year)
                data.Write()
            elif mix_as_obs:
                mix_file, mix_data = mix_as_obs.split(':')
                mix_file = ROOT.TFile(mix_file, 'READ')
                mix_data = self.rebin(mix_file.Get(mix_data.format(year = year) + '/data_obs'), rebin)
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
                for i,coupling in enumerate(self.couplings.basis):
                    name = signal + self.couplings.get_filename(point= 'p', **coupling)[:-1].replace('C3', 'kl') + '_hbbhbb'
                    # name = signal + self.couplings.get_filename(point= 'p', **coupling)[:-1].replace('C3', 'kl').replace('C2V', 'C2' + signal[0]) + '_hbbhbb'
                    name = name.replace('p0_','_')
                    signal_hist = signal_mc[i]
                    signal_hist.SetNameTitle(name,name+"_"+year)
                    signal_hist.Write()
                    for syst in signal_systs.keys():
                        signal_systs[syst][i].SetNameTitle(name+'_'+syst.format(**format_args),name+"_"+syst.format(**format_args))
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
                        weights = self.couplings.generate_weight(**coupling)
                        signal_4b_SR[self.couplings.get_caption(**coupling)] = self.sum_hists(signal_mc, weights)

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
                    ploter_yield = histogram_1d_collection(output_path, title='Signal & Background Yield', tag='_yield')
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
                    title = self.couplings.get_filename(**coupling)[1:-1]
                    hist_path = output_path+title
                    ploter_acc_eff_rela = histogram_1d_collection(hist_path, title='Acc#times Eff ' + title, tag='AccxEff_relative',x_label='Truth m_{4b}', y_label='Relative Acceptance #times Efficiency', y_range=[0,1], smooth= True)
                    ploter_acc_eff = histogram_1d_collection(hist_path, title='Acc#times Eff ' + title, tag='AccxEff',x_label='Truth m_{4b}', y_label='Acceptance #times Efficiency', smooth=True)
                    ploter_acc_eff_count = histogram_1d_collection(hist_path, title='Acc#times Eff ' + title, tag='Count',x_label='Truth m_{4b}', y_label='Events')
                    weights= self.couplings.generate_weight(**coupling)
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


if __name__ == '__main__':
    # basis = [{},{'cv':0.5},{'cv':1.5},{'c2v':0.0},{'c2v':2.0},{'c3':0.0},{'c3':2.0},{'c3':20.0}]
    with plots() as producer:
        producer.debug_mode(True)
        
        # binning = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70 ,0.78, 0.86, 0.93, 0.97, 0.99, 1.00]
        binning = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70 ,0.80, 0.90, 0.95, 1.00]
        # POI
        producer.add_couplings(cv=1.0,c2v=1.0, c3=20)
        producer.add_couplings(cv=1.0,c2v=20, c3=1.0)
        producer.add_couplings(cv=1.0,c2v=1.0, c3=1.0)
        # MC
        # producer.add_couplings(cv=1.0,c2v=1.0, c3=1.0)
        # producer.add_couplings(cv=1.0,c2v=2.0, c3=1.0)
        # producer.add_couplings(cv=1.0,c2v=0.0, c3=1.0)
        # producer.add_couplings(cv=1.0,c2v=1.0, c3=2.0)
        # producer.add_couplings(cv=1.0,c2v=1.0, c3=0.0)
        # producer.add_couplings(cv=1.5,c2v=1.0, c3=1.0)
        # producer.add_couplings(cv=0.5,c2v=1.0, c3=1.0)
        # producer.add_couplings(cv=1.0,c2v=1.0, c3=20.0)

        # producer.compare_histfile('pass*/fourTag/mainView/HHSR/SvB_MA_VHH_ps[_BDT_kl|_BDT_kVV]', {'{}':'14, no k-fold', '{}_14':'14, k-fold','{}_14n':'14, k-fold + norm sample','{}_14nc':'14, k-fold + norm coupling', '{}_8':'8, k-fold','{}_8n':'8, k-fold + norm sample','{}_8nc':'8, k-fold + norm coupling'}, rebin = binning, extra_tag='_all', normalize=True)
        # producer.compare_histfile('pass*/fourTag/mainView/HHSR/SvB_MA_VHH_ps[|_BDT_kl|_BDT_kVV]', {'{}_8':'8, k-fold','{}_8n':'8, k-fold + norm sample','{}_8nc':'8, k-fold + norm coupling'}, rebin = binning, extra_tag='_8features', normalize=True)
        # producer.add_dir(['pass*/fourTag/mainview/[notSR|HHSR|CR|SB]/n*','pass*/fourTag/mainview/[notSR|HHSR|CR|SB]/[can*|*dijet*]/[m*|pt*|*dr*]'])
        # producer.add_dir(['pass*/fourTag/mainview/CR/nSel*'])
        # producer.add_dir(['pass*/fourTag/mainview/CR/[can*|*dijet*|v4j]/[eta|phi|dR|m*|pt*]'])
        # producer.add_dir(['passMV/fourTag/mainView/CR/kl_BDT'])
        # producer.add_dir(['pass*/fourTag/*view*/[HHSR|HHmSR|inclusive]/[m4j|m6j]*','pass*/fourTag/*view*/[HHSR|HHmSR|inclusive]/lead*subl*','pass*/fourTag/*view*/[HHSR|inclusive]/bdt_vs*'])
        # producer.add_dir(['pass*/fourTag/mainView/[HHSR|inclusive|notSR]/puIdSF'])
        # producer.add_dir(['pass*/fourTag/mainView/HHSR/*Jet*/[puId|jetId]'], normalize = True)
        # producer.add_dir(['pass*/threeTag/mainView/TTCR/nSel*'])
        # producer.add_dir(['passMV/fourTag/mainView/HHSR/kl_BDT'], normalize = True)
        producer.add_plot_rule(plot_rule([(0,'passMV')],["self.set_topright('Pass m_{V_{jj}}')"]))
        producer.add_plot_rule(plot_rule([(0,'passMDRs')],["self.set_topright('Pass #Delta R(j,j)')"]))
        producer.add_plot_rule(plot_rule([(3,'HHSR')],["self.set_topmid('HH Signal Region')"]))
        producer.add_plot_rule(plot_rule([(3,'SR')],["self.set_topmid('Inclusive Signal Region')"]))
        producer.add_plot_rule(plot_rule([(3,'CR')],["self.set_topmid('Control Region')"]))
        # producer.plot_1d(1)
        # producer.plot_2d()
        # producer.add_dir(['passMV/fourTag/mainView/HHSR/SvB_MA_VHH_ps_BDT_[kl|kVV]'], normalize = True)
        # producer.add_dir(['pass*/fourTag/mainview/CR/SvB_MA_VHH_ps_BDT_[kl|kVV]'])
        # producer.plot_1d(binning)

        # producer.optimize('passNjOth/fourTag/mainView/HHSR/canJet3BTag')
        # producer.optimize('passMV/fourTag/mainView/HHSR/canJet3BTag')

        # cuts=[('jetMultiplicity','N_{j}#geq 4'), ('bTags','N_{b}#geq 4'), ('MDRs','#Delta R_{jj}'), ('MV','m_{V}'),('MV_HHSR','SR'),('MV_HHSR_HLT','HLT')]
        # cuts=[('jetMultiplicity','N_{j}#geq 4'), ('bTags','N_{b}#geq 4'), ('LooseMDRs','Loose #Delta R_{jj}'), ('LooseMV','Loose m_{V}'),('LooseMV_HHmSR','modified SR'),('LooseMV_HHmSR_HLT','HLT')]
        # producer.AccxEff(cuts)


# systematics
# CMS_btag_<x> x = jes, lf, hf, lfstats1, lfstats2, hfstats1, hfstats2, cferr1, cferr2
# CMS_res_<x>  x = e, m, t, g, j, met(, b) for electrons, muons, hadronic taus, photons, jets, missing energy (and b-jets if you have something specific for those)
# CMS_scale_<x>  x = e, m, t, g, j, met(, b)
# CMS_eff_<x> x = e, m, t, g, j, b for electrons, muons, hadronic taus, photons, jets and b-tagging  trigger efficiencies
        MC_systs = [
            # btag
            systematic([(0,3), (4, '+{}_down_lf')],  'CMS_btag_LF_2016_2017_2018Down'),
            systematic([(0,3), (4, '+{}_up_lf')],    'CMS_btag_LF_2016_2017_2018Up'),
            systematic([(0,3), (4, '+{}_down_hf')],  'CMS_btag_HF_2016_2017_2018Down'),
            systematic([(0,3), (4, '+{}_up_hf')],    'CMS_btag_HF_2016_2017_2018Up'),
            systematic([(0,3), (4, '+{}_down_hfstats2')],    'CMS_btag_hfstats2_{year}Down'),
            systematic([(0,3), (4, '+{}_up_hfstats2')],    'CMS_btag_hfstats2_{year}Up'),
            systematic([(0,3), (4, '+{}_down_lfstats2')],    'CMS_btag_lfstats2_{year}Down'),
            systematic([(0,3), (4, '+{}_up_lfstats2')],    'CMS_btag_lfstats2_{year}Up'),
            systematic([(0,3), (4, '+{}_down_hfstats1')],    'CMS_btag_hfstats1_{year}Down'),
            systematic([(0,3), (4, '+{}_up_hfstats1')],    'CMS_btag_hfstats1_{year}Up'),
            systematic([(0,3), (4, '+{}_down_lfstats1')],    'CMS_btag_lfstats1_{year}Down'),
            systematic([(0,3), (4, '+{}_up_lfstats1')],    'CMS_btag_lfstats1_{year}Up'),
            systematic([(0,3), (4, '+{}_down_cferr1')],    'CMS_btag_cferr1_2016_2017_2018Down'),
            systematic([(0,3), (4, '+{}_up_cferr1')],    'CMS_btag_cferr1_2016_2017_2018Up'),
            systematic([(0,3), (4, '+{}_down_cferr2')],    'CMS_btag_cferr2_2016_2017_2018Down'),
            systematic([(0,3), (4, '+{}_up_cferr2')],    'CMS_btag_cferr2_2016_2017_2018Up'),
            systematic([(0,3), (4, '+{}_down_puId')],    'CMS_eff_j_PUJET_id_{year}Down'),
            systematic([(0,3), (4, '+{}_up_puId')],    'CMS_eff_j_PUJET_id_{year}Up'),
            #  JEC
            systematic([(0,3), (4, '+{}_ONNX')],    'CMS_res_j_{year}Up',   'hists_jerUp'),
            systematic([(0,3), (4, '+{}_ONNX')],    'CMS_res_j_{year}Down', 'hists_jerDown'),
            systematic([(0,3), (4, '+{}_ONNX_up_jes')],    'CMS_scale_j_{year}Up',   'hists_jesTotalUp'),
            systematic([(0,3), (4, '+{}_ONNX_down_jes')],    'CMS_scale_j_{year}Down',   'hists_jesTotalDown'),
            # ZHH NNLO
            systematic([(0,3), (4, '+{}_up_NNLO')],    'CMS_scale_ZHH_NNLOUp',   'hists', ['VHH', 'ZHH']),
            systematic([(0,3), (4, '+{}_down_NNLO')],    'CMS_scale_ZHH_NNLODown', 'hists', ['VHH', 'ZHH']),
        ]

        ## make combine shape
        classifier_name = 'SvB_MA_VHH' # SvB_MA_labelBDT
        ## plot systs
        # for tag in ['_jes', '_lf', '_hf', '_hfstats2', '_lfstats2']:
        #     producer.plot_syst('passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps_central', 
        #     {'central':systematic([(0,-1)]),'down':systematic([(0,3), (4,'=down{tag}/central'.format(tag = tag))]),'up':systematic([(0,3), (4,'=up{tag}/central'.format(tag = tag))])},
        #     tag, binning)
        # for tag in ['_jer']:
        #     producer.plot_syst('passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps', 
        #     {'central':systematic([(0,-1)]),'down':systematic([(0,3), (4,'+{}_ONNX')], filename = 'hists'+ tag + 'Down'),'up':systematic([(0,3), (4,'+{}_ONNX')], filename = 'hists'+ tag + 'Up')},
        #     tag, binning)
        # for tag in ['_jesTotal']:
        #     producer.plot_syst('passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps', 
        #     {'central':systematic([(0,-1)]),'down':systematic([(0,3), (4,'+{}_ONNX_down_jes')], filename = 'hists'+ tag + 'Down'),'up':systematic([(0,3), (4,'+{}_ONNX_up_jes')], filename = 'hists'+ tag + 'Up')},
        #     tag, binning)
        # for tag in ['_jer', '_jesTotal']:
        #     producer.plot_syst(['pass*/fourTag/mainView/[inclusive|HHSR]/[sel|can|oth]Jet*/*GenDiff'], 
        #     {'central':systematic([(0,-1)]),'down':systematic([(0,-1),], filename = 'hists'+ tag + 'Down'),'up':systematic([(0,-1)], filename = 'hists'+ tag + 'Up')},
        #     tag)
        # producer.plot_syst(['passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps_nom'], 
        # {'central':systematic([(0,-1)]),'down':systematic([(0,3), (4,'=down/nom')], filename = 'hists'),'up':systematic([(0,3), (4,'=up/nom')], filename = 'hists')},'_puId')
        # producer.plot_syst(['passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps'], 
        # {'central':systematic([(0,-1)]),'down':systematic([(0,3), (4,'+{}_down_NNLO')], filename = 'hists'),'up':systematic([(0,3), (4,'+{}_up_NNLO')], filename = 'hists')},'_ZHH_NNLO_reweight', binning)
        
        # # kVV enhanced region
        producer.save_shape('shapefile_VhadHH_SR_{year}_kVV', 'passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps_BDT_kVV', MC_systs, binning)
        # producer.save_shape('shapefile_VhadHH_CR_{year}_kVV', 'passMV/fourTag/mainView/CR/'+classifier_name+'_ps_BDT_kVV', MC_systs, binning, unblind = True)
        producer.save_shape('shapefile_VhadHH_SB_{year}_kVV', 'passMV/fourTag/mainView/SB/'+classifier_name+'_ps_BDT_kVV', MC_systs, binning, unblind = True)
        # # kl  enhanced region
        producer.save_shape('shapefile_VhadHH_SR_{year}_kl', 'passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps_BDT_kl', MC_systs, binning)
        # producer.save_shape('shapefile_VhadHH_CR_{year}_kl', 'passMV/fourTag/mainView/CR/'+classifier_name+'_ps_BDT_kl', MC_systs, binning, unblind = True)
        producer.save_shape('shapefile_VhadHH_SB_{year}_kl', 'passMV/fourTag/mainView/SB/'+classifier_name+'_ps_BDT_kl', MC_systs, binning, unblind = True)

        # for i in range(10):
        #     mix_n = str(i)
        #     producer.save_shape('shapefile_VhadHH_Mix'+mix_n+'_{year}_kl', 'passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps_BDT_kl', MC_systs, binning, mix_as_obs = 'ZZ4b/nTupleAnalysis/combine/hists_VHH_closure_3bDvTMix4bDvT_HHSR_weights_nf8_HH.root:3bDvTMix4bDvT_v'+mix_n+'/VHH_ps_lbdt{year}')
        #     producer.save_shape('shapefile_VhadHH_Mix'+mix_n+'_{year}_kVV', 'passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps_BDT_kVV', MC_systs, binning, mix_as_obs = 'ZZ4b/nTupleAnalysis/combine/hists_VHH_closure_3bDvTMix4bDvT_HHSR_weights_nf8_HH.root:3bDvTMix4bDvT_v'+mix_n+'/VHH_ps_sbdt{year}')

        ## make signal templates
        # producer.add_dir(['passMV/fourTag/mainView/HHSR/'+classifier_name+'_ps_BDT_[kl|kVV]'])
        # producer.save('signal_templates')

        # make PU Jet ID SF
        # selection = 'passPreSel'
        # producer.make_PUJetID_SF([selection + '/threeTag/mainView/TTCR/allBJets',
        # selection + '/threeTag/mainView/TTCR/allNotBJets', 
        # selection + '/threeTag/mainView/TTCR/allPUBJets', 
        # selection + '/threeTag/mainView/TTCR/allPUNotBJets'],
        # [selection + '/threeTag/mainView/TTCR/allBJetsPassPuId',
        # selection + '/threeTag/mainView/TTCR/allNotBJetsPassPuId', 
        # selection + '/threeTag/mainView/TTCR/allPUBJetsPassPuId', 
        # selection + '/threeTag/mainView/TTCR/allPUNotBJetsPassPuId'], 'puJetIdSF',
        # ['b','cudsg','bMisTag','cudsgMisTag'], rebin_x = 1, rebin_y = 1)
