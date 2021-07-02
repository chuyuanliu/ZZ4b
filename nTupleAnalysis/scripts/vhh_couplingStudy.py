from os import error
import os
import tkinter
import json
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.widgets import Slider, Button
from datetime import datetime
import gc

DEFAULT_SAVE_PATH = './saved_couplings'
DEFAULT_BASIS = [{'cv':0.5},{'cv':1.5},{'c2v':2.0},{'c2v':0.0},{'c3':2.0},{'c3':0.0}]

cp_labels = ['cv', 'c2v', 'c3']

class coupling:
    point = '.'
    def __init__(self, scan_cps, basis_cps = [],):
        self.scan_diagram_weight = self.get_diagram_weight_batch(scan_cps.shape, scan_cps.cv, scan_cps.c2v, scan_cps.c3)
        self.basis = []
        self.transmat = None
        for basis in basis_cps:
            self.add_basis(**basis)
        cps_whh = [{'cv':0.5},{'cv':1.5},{'c2v':2.0},{'c2v':0.0},{'c3':2.0},{'c3':0.0}]
        xsecs_whh = [2.870e-04, 8.902e-04, 1.115e-03, 1.491e-04, 6.880e-04, 2.371e-04]
        self.xsec_whh_component = self.get_diagram_xsec(cps_whh, xsecs_whh)
        
    def get_diagram_xsec(self, cps, xsecs):
        mat = np.empty((6, 6))
        for i in range(6):
            mat[i][:]=self.get_diagram_weight(**cps[i])
        mat = np.linalg.pinv(mat)
        xsecs = np.array(xsecs)
        return np.matmul(mat, xsecs)

    def estimate_xsec_whh(self):
        weight = self.get_weight()
        xsec = np.matmul(self.mat, self.xsec_whh_component)
        return np.matmul(weight , xsec)
    def estimate_error_whh(self):
        weight = self.get_weight()
        xsec = np.matmul(self.mat, self.xsec_whh_component)
        return np.sqrt(np.matmul(weight * weight, xsec))

    def get_float(self, str):
        return float(str.replace(self.point,'.'))
    def get_str(self, num):
        return '{:.2f}'.format(num).replace('.', self.point)
    def get_title(self, n):
        result = ''
        for i in range(3):
            result += cp_labels[i] + '=' + self.get_str(self.basis[n][cp_labels[i]]) + ', '
        return result[:-2]

    def get_diagram_weight(self, cv = 1.0, c2v = 1.0, c3 = 1.0):
        return np.array([cv**2 * c3**2, cv**4, c2v**2, cv**3 * c3, cv * c3 * c2v, cv**2 * c2v])
    def get_diagram_weight_batch(self, shape, cv, c2v, c3):
        new_shape = shape + (6,)
        result = np.empty(new_shape)
        result[...,0] = cv**2 * c3**2
        result[...,1] = cv**4
        result[...,2] = c2v**2
        result[...,3] = cv**3 * c3
        result[...,4] = cv * c3 * c2v
        result[...,5] = cv**2 * c2v
        return result

    def get_transmat(self):
        count = self.n_basis()
        if count>=6:
            self.mat = np.empty((count, 6))
            for i in range(count):
                self.mat[i][:]=self.get_diagram_weight(**self.basis[i])
            self.transmat = np.linalg.pinv(self.mat)
    def add_basis(self, cv = 1.0, c2v = 1.0, c3 = 1.0):
        self.basis.append({'cv':cv, 'c2v':c2v, 'c3':c3})
        self.get_transmat()
    def set_basis(self, n, cv = 1.0, c2v = 1.0, c3 = 1.0):
        if n < len(self.basis):
            self.basis[n]['cv'] = cv
            self.basis[n]['c2v'] = c2v
            self.basis[n]['c3'] = c3
            self.get_transmat()

    def get_weight(self):
        if self.transmat is not None:
            return np.round(np.matmul(self.scan_diagram_weight, self.transmat), 15)

    def n_basis(self):
        return len(self.basis)

class scan:
    def __init__(self, min, max, step):
        c2v = np.arange(min, max, step)
        c3 = np.arange(min, max, step)
        self.c2v, self.c3 = np.meshgrid(c2v, c3)
        self.shape = self.c2v.shape
        self.cv = np.ones(self.shape)

def subaxes(ax, y, width_ratio, height):
    width = ax.get_position().width
    return plt.axes([ax.get_position().x0, ax.get_position().y0 - y, width * width_ratio, height])

def plot_weights(transform, vmax = 1e3, thresh =1e-2, summed = False, nbasis = 6, initbasis = DEFAULT_BASIS):
    return_args = None
    shape = (2,4)
    fig, axes = plt.subplots(shape[0], shape[1], figsize = (17,8))
    fig.tight_layout()
    fig.subplots_adjust(bottom = 0.1, top = 0.97, hspace = 0.3, right = 0.90)
    color_args = {'norm':colors.SymLogNorm(linthresh=thresh, linscale=thresh, vmin=-vmax, vmax=vmax, base=10), 'cmap':'RdBu_r'}

    scans = scan(-10.0, 10.0, 0.2)
    basis = initbasis
    for i in range(nbasis-len(initbasis)):
        basis.append({})
    cp_weights = coupling(scans, basis)
    cp_init = cp_weights.basis
    sliders = np.empty(shape, dtype = 'O')
    subplots = np.empty(shape, dtype = 'O')
    for row in range(shape[0]):
        for col in range(shape[1]):
            n = row * shape[1] + col
            sliders[row, col] = {}
            if(n < cp_weights.n_basis()):
                for i in range(3):
                    sliders[row, col][cp_labels[i]] = Slider(subaxes(axes[row, col], 0.04 + i * 0.02, 0.8, 0.01), cp_labels[i], -10, 10, valinit = cp_init[n][cp_labels[i]])
    weight = transform(cp_weights.get_weight())
    for row in range(shape[0]):
        for col in range(shape[1]):
            n = row * shape[1] + col
            if(n < cp_weights.n_basis()):
                axes[row, col].title.set_text(cp_weights.get_title(n))
                if not summed:
                    subplots[row, col] = axes[row, col].pcolor(scans.c2v,scans.c3,weight[:,:,n], **color_args)
                elif n == 0:
                    subplots[row, col] = axes[row, col].pcolor(scans.c2v,scans.c3,weight[:,:], **color_args)
                if not summed or (summed and n == 0):
                    fig.colorbar(subplots[row, col], ax=axes[row, col])
                    axes[row,col].set_xlabel('c2v')
                    axes[row,col].xaxis.set_label_coords(1.02, -0.02)
                    axes[row,col].set_ylabel('c3')
                    axes[row,col].yaxis.set_label_coords(-0.01, 1.02)

    def update(val):
        for row in range(shape[0]):
            for col in range(shape[1]):
                n = row * shape[1] + col
                if(n < cp_weights.n_basis()):
                    slider = sliders[row, col]
                    cp_weights.set_basis(n, cv = slider['cv'].val,  c2v = slider['c2v'].val,  c3 = slider['c3'].val)
        weight = transform(cp_weights.get_weight())
        for row in range(shape[0]):
            for col in range(shape[1]):
                n = row * shape[1] + col
                if(n < cp_weights.n_basis()):
                    axes[row, col].title.set_text(cp_weights.get_title(n))
                    if not summed:
                        subplots[row, col].set_array(weight[:-1, :-1, n].ravel())
                    elif n == 0:
                        subplots[row, col].set_array(weight[:-1, :-1].ravel())

    for row in range(shape[0]):
        for col in range(shape[1]):
            n = row * shape[1] + col
            if(n < cp_weights.n_basis()):
                for key in cp_labels:
                    sliders[row, col][key].on_changed(update)

    def add(event):
        if nbasis < 8:
            nonlocal return_args
            return_args = {'transform':transform, 'vmax':vmax, 'thresh':thresh, 'summed':summed, 'nbasis': nbasis + 1, 'initbasis':cp_weights.basis}
            plt.close()
    def remove(event):
        if nbasis >6:
            nonlocal return_args
            return_args = {'transform':transform, 'vmax':vmax, 'thresh':thresh, 'summed':summed, 'nbasis': nbasis - 1, 'initbasis':cp_weights.basis[:-1]}
            plt.close()
    def save(event):
        if not os.path.isdir(DEFAULT_SAVE_PATH):
            os.mkdir(DEFAULT_SAVE_PATH)
        root = tkinter.Tk()
        root.withdraw() 
        filename = filedialog.asksaveasfilename(parent=root, initialfile = datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), initialdir=DEFAULT_SAVE_PATH, title='Save')
        if filename != '':
            fig.savefig(filename + '.png')
            file = open (filename + '.json', 'w')
            file.write(json.dumps(cp_weights.basis, indent=4))
            file.close()
        root.destroy()
    def load(event):
        if not os.path.isdir(DEFAULT_SAVE_PATH):
            os.mkdir(DEFAULT_SAVE_PATH)
        root = tkinter.Tk()
        root.withdraw() 
        filename = filedialog.askopenfilename(parent=root, initialdir=DEFAULT_SAVE_PATH, title='Load', filetypes=[('JSON File','.json')])
        if filename != '':
            file = open (filename, 'r')
            new_basis = json.loads(file.read())
            file.close()
            nonlocal return_args
            return_args =  {'transform':transform, 'vmax':vmax, 'thresh':thresh, 'summed':summed, 'nbasis': len(new_basis), 'initbasis':new_basis}
            plt.close()
        root.destroy()
    def reset(event):
        for row in range(shape[0]):
            for col in range(shape[1]):
                n = row * shape[1] + col
                if(n < cp_weights.n_basis()):
                    for key in cp_labels:
                        sliders[row, col][key].reset()
    reset_button = Button(plt.axes([0.95, 0.94, 0.05, 0.03]), 'Reset')
    reset_button.on_clicked(reset)
    add_button = Button(plt.axes([0.95, 0.54, 0.05, 0.03]), 'Add')
    add_button.on_clicked(add)
    remove_button = Button(plt.axes([0.95, 0.50, 0.05, 0.03]), 'Remove')
    remove_button.on_clicked(remove)
    save_button = Button(plt.axes([0.95, 0.46, 0.05, 0.03]), 'Save')
    save_button.on_clicked(save)
    load_button = Button(plt.axes([0.95, 0.42, 0.05, 0.03]), 'Load')
    load_button.on_clicked(load)
    plt.show()
    del fig
    del axes
    del subplots
    del sliders
    del reset_button
    del add_button
    del remove_button
    del save_button
    del load_button
    del cp_weights
    del weight
    del scans
    del color_args
    gc.collect()
    return return_args

def coupling_study(transform, vmax = 1e3, thresh =1e-2, summed = False, nbasis = 6, initbasis = DEFAULT_BASIS):
    return_args = {'transform':transform, 'vmax':vmax, 'thresh':thresh, 'summed':summed, 'nbasis': nbasis, 'initbasis':initbasis}
    while return_args is not None:
        return_args = plot_weights(**return_args)

def raw(weight):
    return weight
def sum_negative2(weight):
    negative = weight * (weight<0)
    return np.sqrt(np.sum(negative * negative, axis=2))
def sum_negative2_relative(weight):
    negative = weight * (weight<0)
    return np.sqrt(np.sum(negative * negative, axis=2))/np.sqrt(np.sum(weight * weight, axis=2))


# show all weights
# coupling_study(raw)

# sum(negative^2)/sum(weight^2)
coupling_study(sum_negative2_relative, 1, 1e-3, summed = True)

# sum(negative^2)
# coupling_study(sum_negative2, summed = True)