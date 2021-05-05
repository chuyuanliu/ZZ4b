def F2Str(f, dot = '_'):
    return '{:.1f}'.format(f).replace('.', dot)

def getCoupling(CV = '1_0', C2V = '1_0', C3 = '1_0'):
    coupling = 'CV_' + CV + '_C2V_' + C2V + '_C3_' + C3
    files = []
    for V in ['Z', 'W', 'V']:
        files.append(V + 'HHTo4B_' + coupling + '_')
    files.append(coupling)
    return files

def getCouplingList(couplings):
    files = []
    couplings = couplings.split(',')
    for coupling in couplings:
        scales = {}
        if coupling != '':
            coupling = coupling.split(';')
            for scale in coupling:
                scale = scale.split(':')
                scales[scale[0]] = scale[1]
        files.append(getCoupling(**scales))
    return files

def xrdcpFiles(src, dest, dirs, files):
    script = open('copy.sh', 'w')
    for dir in dirs:
        script.write('mkdir ' + dest + dir + '\n')
        for file in files.keys():
            script.write('xrdcp root://cmseos.fnal.gov/'+ src + dir + file + ' ' + dest + dir + files[file] + '\n')
    script.close()