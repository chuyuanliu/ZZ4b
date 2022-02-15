from copy import copy
from math import sqrt
import numpy as np
import ROOT
import re
import os, shutil
import getpass
import sys
import array

from numpy.lib.ufunclike import fix
sys.path.insert(0, '.')
import Helper.ROOTCanvas as canvas_helper

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning
ROOT.gStyle.SetPalette(ROOT.kRainBow)
ROOT.gStyle.SetGridStyle(2)
ROOT.gStyle.SetHatchesLineWidth(1)

USER = getpass.getuser()
in_path = '/uscms/home/'+USER+'/nobackup/VHH/'
out_path = in_path + 'plots/'
years = ['RunII']
signals = ['VHH']
no_background = False #temp
event_count = True
signal_scale = 50

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

class plot_rule:
    def __init__(self):
        None

# Plot

class histogram_1d_collection:
    def __init__(self, path, title = '', tag = '', normalize = False, x_label = '', y_label = '', y_range = None, smooth = False):
        self.path = path
        self.title = title
        self.tag = tag
        self.normalize = normalize

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

    def add_hist(self, hist, tag, scale = 1, line_color = 1):
        if not isinstance(hist, ROOT.TH1F) and not isinstance(hist, ROOT.TH1D):
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

    def plot(self):
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
        canvas_gen = canvas_helper.ROOTCanvas(self.x_min, self.x_max, self.y_min, self.y_max * 1.05)
        canvas_gen.XLabel.Text = self.set_font(self.x_label)
        canvas_gen.YLabel.Text = self.set_font(self.y_label)
        canvas_gen.AllowLegend = True
        canvas_gen.AllowRatio  = allow_ratio
        canvas = canvas_gen.GetCanvas(self.title)
        canvas_gen.MainPad.cd()
        self.background.Draw('SAME HIST')
        if self.data is not None:
            self.data.Draw('SAME P E')
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
                self.signals[signal].Draw('SAME HIST PLC')
        canvas_gen.Legend.cd()
        self.legend.Draw()
        if allow_ratio: # TEMP
            ratio_range = 0.1
            ratio = self.data.Clone()
            bkgd = self.ttbar.Clone()
            bkgd.Add(self.multijet)
            bkgd_error = bkgd.Clone()
            n_bins = bkgd.GetNbinsX()
            for i in range(1, n_bins):
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
        canvas.Print(self.path + self.tag + '.pdf')
       
class histogram_2d_collection:
    def __init__(self, path, title, tag = '', x_label = '', y_label = '', z_label = ''):
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

    def add_curve(self, curve, levels = [], range = [None, None]):
        if len(levels) == 0:
            x_min = self.x_min if range[0] is None else max(self.x_min, range[0])
            x_max = self.x_max if range[1] is None else min(self.x_max, range[1])
            curve = ROOT.TF1('range', curve, x_min, x_max)
            curve.SetLineColor(ROOT.kRed)
            self.curves.append(curve)
        else:
            curve = ROOT.TF2('range', curve, self.x_min, self.x_max, self.y_min, self.y_max)
            contour = array.array('d')
            for level in levels:
                contour.append(level)
            curve.SetContour(len(levels), contour)
            curve.SetLineColor(ROOT.kRed)
            self.curves.append(curve)

    def add_hist(self, hist, tag):
        if not isinstance(hist, ROOT.TH2F) and not isinstance(hist, ROOT.TH2D):
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

    def plot(self):
        for tag in self.hists:
            canvas = ROOT.TCanvas(self.title + tag, self.title, 1400, 800)
            self.hists[tag].Draw('COLZ')
            for curve in self.curves:
                curve.Draw('SAME')
            canvas.Print(self.path + tag + self.tag + '.pdf')

class plots:
    def __init__(self, match_all_dirs = True, ignore_case = True, debug = False, cmd_length =20):
        self.lumi = {'2016':  '36.3e3',#35.8791
                    '2016_preVFP': '19.5e3',
                    '2016_postVFP': '16.5e3',
                    '2017':  '36.7e3',#36.7338
                    '2018':  '59.8e3',#59.9656
                    '17+18': '96.7e3',
                    'RunII':'132.8e3',
                    }

        self.debug = debug
        self.cmd_length = cmd_length

        self.input = in_path
        self.output = out_path
        self.years = years
        self.signals = signals
        self.hists_tag = '_j_r'

        self.path = {}
        self.all_hists = {}
        self.plot_hists = {}
        self.plot_couplings = []

        self.signal_files = {}
        self.data_files_4b = {}
        self.data_files_3b = {}
        self.ttbar_files = {}
        self.multijet_files = {}

        self.couplings = coupling_weight_generator([{},{'cv':0.5},{'cv':1.5},{'c2v':0.0},{'c2v':2.0},{'c3':0.0},{'c3':2.0},{'c3':20.0}], debug = debug, cmd_length = cmd_length)
        self.match = wildcard_match(match_all_dirs, ignore_case, debug = debug, cmd_length = cmd_length)
        self.base_path = path_extensions(self.output, clean = True, debug = debug, cmd_length = cmd_length)

        for year in self.years:
            self.signal_files[year] = {}
            self.path[year] = {}
            for signal in self.signals:
                self.signal_files[year][signal] = []
                self.path[year][signal] = path_extensions(self.output + year + signal + '/', clean = True, debug = debug, cmd_length = cmd_length)
        
        for year in self.years:
            self.data_files_4b[year] = ROOT.TFile(self.input + 'data' + year + '_4b/hists' + self.hists_tag + '.root')
            self.data_files_3b[year] = ROOT.TFile(self.input + 'data' + year + '_3b/hists' + self.hists_tag + '.root')
            self.ttbar_files[year] = ROOT.TFile(self.input + 'TT' + year + '_4b/hists' + self.hists_tag + '.root')
            for signal in self.signals:
                for coupling in self.couplings.get_all_filenames():
                    root_path = self.input + signal + 'To4B' + coupling + year + '/hists.root'
                    if os.path.isfile(root_path):
                        self.signal_files[year][signal].append(ROOT.TFile(root_path))
                    else:
                        self.signal_files[year][signal].append(None)
        self.root_dir = self.data_files_4b[self.years[0]].GetDirectory('')
        self.modify_plot_hists_list_recursive('', self.initialize_hist)

        # TODO add intelligent color
        # TODO add html viewer
        # TODO add plot coupling from string
        # TODO add ratio
        # TODO add rebinning            
        # TODO rewrite add/remove logic (async)
        # TODO add plot rules
        # TODO RAM management

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.system('tar -C ' + self.input + ' -cvf ' + self.input + 'plots.tar.gz plots/')
        for year in self.years:
            if self.debug: print('Close'.ljust(self.cmd_length) + self.data_files_4b[year].GetName())
            self.data_files_4b[year].Close()
            if self.debug: print('Close'.ljust(self.cmd_length) + self.data_files_3b[year].GetName())
            self.data_files_3b[year].Close()
            if self.debug: print('Close'.ljust(self.cmd_length) + self.ttbar_files[year].GetName())
            self.ttbar_files[year].Close()
            for signal in self.signals:
                for file in self.signal_files[year][signal]:
                    if file is not None:
                        if self.debug: print('Close'.ljust(self.cmd_length) + file.GetName())
                        file.Close()

            
    
    # internal methods
    
    ## hists operation

    def join_hist_path(self, path):
        return '/'.join(path)

    def sum_hists(self, hists, weights):
        sum = hists[0].Clone()
        sum.Scale(weights[0])
        for i in range(1,len(hists)):
            sum.Add(hists[i],weights[i])       
        return sum

    def load_signal_mc_hists(self, year, signal, hist, rebin = 1):
        hists = []
        for file in self.signal_files[year][signal]:
            if file is None:
                return None
            else:
                signal = file.Get(hist).Clone()
                if not rebin == 1:
                    signal.Rebin(rebin) #rebin
                hists.append(signal)
        return hists

    def load_ttbar_mc_hists(self, year, hist, rebin = 1):
        if self.ttbar_files[year] is None:
            return None
        ttbar = self.ttbar_files[year].Get(hist).Clone()
        ttbar.Rebin(rebin) #rebin
        return ttbar

    def load_data_hists(self, year, hist, rebin = 1):
        if self.data_files_4b[year] is None:
            return None
        data = self.data_files_4b[year].Get(hist).Clone()
        data.Rebin(rebin) #rebin
        return data

    def load_multijet_hists(self, year, hist, rebin = 1):
        if self.data_files_3b[year] is None:
            return None
        path = copy(self.all_hists[hist])
        path[1] = 'threeTag'
        path = self.join_hist_path(path)
        if self.hists_tag == '_j':
            hist_multijet = self.data_files_3b[year].Get(path).Clone()
            hist_ttbar = self.ttbar_files[year].Get(path).Clone()
            hist_multijet.Add(hist_ttbar, -1)
            hist_multijet.rebin(rebin)
            return hist_multijet
        else:
            multijet = self.data_files_3b[year].Get(path).Clone()
            multijet.Rebin(rebin)
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
    
    def plot_1d(self, rebin = 1): #TEMP
        for year in self.years:
            for signal in self.signals:
                for hist in self.plot_hists:
                    if self.debug: print('Plot'.ljust(self.cmd_length) + hist) 
                    path = self.path[year][signal].mkdir(self.all_hists[hist][:-1])
                    path += self.all_hists[hist][-1]
                    signal_mc = self.load_signal_mc_hists(year, signal, hist, rebin)
                    if not isinstance(signal_mc[0], ROOT.TH1F) and not isinstance(signal_mc[0], ROOT.TH1D):
                        continue
                    ploter = histogram_1d_collection(path, title=hist, normalize = self.plot_hists[hist],y_label='Events')
                    if not no_background:
                        ploter.add_hist(self.load_data_hists(year, hist, rebin), 'Data ' + self.lumi[year] + ' ' + year)
                        ploter.add_hist(self.load_multijet_hists(year, hist, rebin), 'Multijet Model')
                        ploter.add_hist(self.load_ttbar_mc_hists(year, hist, rebin), 't#bar{t}')
                    if signal_mc is not None:
                        for coupling in self.plot_couplings:
                            weights = self.couplings.generate_weight(**coupling)
                            ploter.add_hist(self.sum_hists(signal_mc, weights), self.couplings.get_caption(**coupling), signal_scale)
                    ploter.plot()

    def plot_2d(self): #TEMP
        for year in self.years:
            for signal in self.signals:
                for hist in self.plot_hists:
                    if self.debug: print('Plot'.ljust(self.cmd_length) + hist) 
                    path = self.path[year][signal].mkdir(self.all_hists[hist])
                    signal_mc = self.load_signal_mc_hists(year, signal, hist)
                    if not isinstance(signal_mc[0], ROOT.TH2F) and not isinstance(signal_mc[0], ROOT.TH2D):
                        continue
                    ploter = histogram_2d_collection(path, title=hist)
                    if not no_background:
                        ploter.add_hist(self.load_data_hists(year, hist), 'Data')
                        ploter.add_hist(self.load_multijet_hists(year, hist), 'Multijet')
                        ploter.add_hist(self.load_ttbar_mc_hists(year, hist), 'TTbar')
                    if signal_mc is not None:
                        for coupling in self.plot_couplings:
                            weights = self.couplings.generate_weight(**coupling)
                            ploter.add_hist(self.sum_hists(signal_mc, weights), self.couplings.get_filename(**coupling))
                    if 'm4j' in hist and 'leadSt' in hist and 'dR' in hist:
                        ploter.add_curve('650.0/x+0.5', range=[None, 650])
                        ploter.add_curve('360.0/x-0.5')
                        ploter.add_curve('1.5', range = [650, None])
                    if 'm4j' in hist and 'sublSt' in hist and 'dR' in hist:
                        ploter.add_curve('650.0/x+0.7', range=[None, 812.5])
                        ploter.add_curve('235.0/x')
                        ploter.add_curve('1.5', range=[812.5, None])
                    if 'leadSt_m' in hist and 'sublSt_m' in hist:
                        ploter.add_curve('(((x-125*1.02)/(0.1*x))**2 +((y-125*0.98)/(0.1*y))**2)',[1.9**2])
                    ploter.plot()

    def compare(self, hists, rebin = 1, normalize = False):
        for year in self.years:
            for signal in self.signals:
                signal_mcs = {}
                for hist in hists:
                    signal_mcs[hist] = self.load_signal_mc_hists(year, signal, hist, rebin)
                filename = '_vs_'.join([self.all_hists[hist][-1] for hist in hists])
                for coupling in self.plot_couplings:
                    path = self.path[year][signal].mkdir(['compare']) + filename + self.couplings.get_filename(**coupling)[:-1]
                    weights = self.couplings.generate_weight(**coupling)
                    ploter = histogram_1d_collection(path, title = filename, normalize = normalize, x_label = 'value')
                    for hist in hists:
                        ploter.add_hist(self.sum_hists(signal_mcs[hist], weights), self.all_hists[hist][-1])
                    ploter.plot()


    def save(self, filename, hist, rebin = 1):
        for year in self.years:
            signal_mc = self.load_signal_mc_hists(year, 'VHH', hist)
            multijet = self.load_multijet_hists(year, hist).Clone()
            multijet.Rebin(rebin)
            multijet.SetNameTitle('multijet_background','multijet_background_'+year)
            ttbar = self.load_ttbar_mc_hists(year, hist).Clone()
            ttbar.Rebin(rebin)
            ttbar.SetNameTitle('ttbar_background','ttbar_background'+year)
            output_file = ROOT.TFile(self.input + filename + year + '.root','recreate')
            for i,coupling in enumerate(self.couplings.basis):
                name = 'VHH' + self.couplings.get_filename(point= 'p', **coupling)[:-1].replace('C3', 'kl') + '_hbbhbb'
                name = name.replace('p0_','_')
                signal = signal_mc[i].Clone()
                signal.Rebin(rebin)
                signal.SetNameTitle(name,name+"_"+year)
                output_file.cd()
                signal.Write()
            output_file.cd()
            multijet.Write()
            output_file.cd()
            ttbar.Write()
            x_axis = ttbar.GetXaxis()
            data = ROOT.TH1F('data_obs','data_obs'+year+'; '+x_axis.GetTitle()+'; Events', ttbar.GetNbinsX(), x_axis.GetXmin(), x_axis.GetXmax() )
            output_file.cd()
            data.Write()
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

                        
                    # output histograms        producer.plot_1d(1)

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
    with plots() as producer:
        producer.debug_mode(True)
        # producer.add_dir(['pass*/fourTag/mainview/[notSR|HHSR|CR|SB]/n*','pass*/fourTag/mainview/[notSR|HHSR|CR|SB]/[can*|*dijet*]/[m*|pt*|*dr*]'])
        producer.add_dir(['pass[mv|mdrs]/fourTag/mainview/[HHSR|CR|SB]/nSel*','pass*/fourTag/mainview/[HHSR|CR|SB]/[can*|*dijet*]/[m*|pt*|*dr*]'])
        # producer.add_dir(['passMV/fourTag/mainview/[HHSR|CR]/*[BDT|SvB_MA*_ps]*'])
        # producer.add_dir(['pass*/fourTag/mainview/HHSR/[can*|*dijet*|lead*|subl*]/[m*|pt*|*dr*]'])
        # producer.add_dir(['pass*/fourTag/*view*/[HHSR|inclusive]/[m4j|m6j]*','pass*/fourTag/*view*/[HHSR|inclusive]/lead*subl*'])
        producer.add_couplings(cv=1.0,c2v=1.0, c3=[-20,20])
        producer.add_couplings(cv=1.0,c2v=[-20,20], c3=1.0)

        # MC
        # producer.add_couplings(cv=1.0,c2v=1.0, c3=1.0)
        # producer.add_couplings(cv=1.0,c2v=2.0, c3=1.0)
        # producer.add_couplings(cv=1.0,c2v=0.0, c3=1.0)
        # producer.add_couplings(cv=1.0,c2v=1.0, c3=2.0)
        # producer.add_couplings(cv=1.0,c2v=1.0, c3=0.0)
        # producer.add_couplings(cv=1.5,c2v=1.0, c3=1.0)
        # producer.add_couplings(cv=0.5,c2v=1.0, c3=1.0)

        # producer.optimize('passNjOth/fourTag/mainView/HHSR/canJet3BTag')
        # producer.optimize('passMV/fourTag/mainView/HHSR/canJet3BTag')

        # cuts=[('jetMultiplicity','N_{j}#geq 4'), ('bTags','N_{b}#geq 4'), ('MDRs','#Delta R_{jj}'), ('NjOth','N_{j}#geq 6'), ('MV','m_{V}'),('MV_HHSR','SR'),('MV_HHSR_HLT','HLT')]
        # producer.AccxEff(cuts)
        # producer.plot_2d()
        producer.plot_1d(1)
        # producer.save('VhadHH_combine_', 'passMV/fourTag/mainView/HHSR/SvB_MA_regionBDT_signalAll_ps', 4)
        # producer.save('VhadHH_combine_labelBDT_', 'passMV/fourTag/mainView/HHSR/SvB_MA_labelBDT_ps', 4)



# UL dataset
# dataset =/*HHTo4B_CV_*_C2V_*_C3_*_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv2*v15*/NANOAODSIM 
# dataset=/*HHTo4B_CV_*_*_C2V_*_0_C3_*_0_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL17NanoAODv2*/NANOAODSIM

# Trigger
# root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/ULTrig/*/picoAOD_wTrigWeights.root
# root://cmseos.fnal.gov//store/user/jda102/condor/ZH4b/ULTrig/data*/picoAOD.root

# NNLO
# /afs/cern.ch/user/c/chayanit/work/public/forVHH/zhh_nnlovslo.root