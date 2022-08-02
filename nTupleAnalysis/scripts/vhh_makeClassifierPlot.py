import numpy as np
import matplotlib.pyplot as plt
import re


varName = 'auc' 
# varName = 'sigma'

itemsPattern = r' \| (\d+\.\d+) \((\d+), (\d+), (\d+), (\d+)\) \|( +)(\d+)\/( +)(\d+) \| (?P<sigma>\d+\.\d+) \| (\d+\.\d+) \| (?P<auc>\d+\.\d+) \|'
trainingPattern = re.compile(r'Training' + itemsPattern)
validationPattern = re.compile(r'Validation' + itemsPattern)

train_style = 'norm'
epochs = 20
nFeatures = np.array([[4, 364], [6, 666], [8, 1052], [10, 1522], [12, 2076], [14, 2714]])
epochX = np.arange(epochs)
logFileName   = '/mnt/d/wsl/VHH/SvB_training/nFeatures{nFeature:d}_{style}_offset{offset:d}_epoch{epochs:d}/SvB_MA_HCR+attention_{nFeature:d}_np{nParameter:d}_seed0_lr0.01_epochs20_offset{offset:d}.log'

data = {} # 0 Training, 1 Validation
data['auc'] = np.zeros([2, nFeatures.shape[0], epochs, 3])
data['sigma'] = np.zeros([2, nFeatures.shape[0], epochs, 3])

for i in range(nFeatures.shape[0]):
    nFeature   = nFeatures[i, 0]
    nParameter = nFeatures[i, 1]
    for offset in range(3):
        with open(logFileName.format(nFeature = nFeature, offset = offset, nParameter = nParameter, epochs = epochs, style = train_style), 'r') as f:
            log = f.read()
            trainingLog = re.finditer(trainingPattern, log)
            for j,match in enumerate(trainingLog):
                data['auc'][0,i,j,offset] = match['auc']
                data['sigma'][0,i,j,offset] = match['sigma']
            validationLog = re.finditer(validationPattern, log)
            for j,match in enumerate(validationLog):
                data['auc'][1,i,j,offset] = match['auc']
                data['sigma'][1,i,j,offset] = match['sigma']

colors = ['tab:red', 'tab:orange', 'gold', 'tab:green','tab:blue','tab:purple']

for var in ['auc', 'sigma']:
    data[var].sort(axis = 3)
    for minEpoch in [0, 10]:
        fig = plt.figure(figsize=(16, 9), dpi=72)
        ax = plt.gca()
        for i in range(nFeatures.shape[0]):
            ax.plot(epochX[minEpoch:], data[var][0,i,minEpoch:,1], '--', color = colors[i], linewidth = 1)
            ax.fill_between(epochX[minEpoch:], data[var][0,i,minEpoch:,0], data[var][0,i,minEpoch:,2], color = colors[i], alpha = 0.2)
            ax.plot(epochX[minEpoch:], data[var][1,i,minEpoch:,1], color = colors[i], label = '{:d}'.format(nFeatures[i,0]), linewidth = 1)
            ax.fill_between(epochX[minEpoch:], data[var][1,i,minEpoch:,0], data[var][1,i,minEpoch:,2], color = colors[i], alpha = 0.5)
        ax.set_xlabel('epoch')
        ax.set_ylabel(var)
        ax.legend()
        fig.savefig('/mnt/d/wsl/VHH/SvB_training/{}_{}_from{:d}.pdf'.format(train_style, var,minEpoch))

for var in ['auc', 'sigma']:
    fig = plt.figure(figsize=(16, 9), dpi=72)
    ax = plt.gca()
    ax.plot(nFeatures[:,0], data[var][0,:,-1,1], '--', label = 'train', color = 'tab:red', linewidth = 1)
    ax.fill_between(nFeatures[:,0], data[var][0,:,-1,0], data[var][0,:,-1,2], color = 'tab:red', alpha = 0.2)
    ax.plot(nFeatures[:,0], data[var][1,:,-1,1], label = 'valid', color = 'tab:blue', linewidth = 1)
    ax.fill_between(nFeatures[:,0], data[var][1,:,-1,0], data[var][1,:,-1,2], color = 'tab:blue', alpha = 0.5)
    ax.set_xlabel('n features')
    ax.set_ylabel(var)
    ax.legend()
    fig.savefig('/mnt/d/wsl/VHH/SvB_training/{}_{}_last.pdf'.format(train_style, var))