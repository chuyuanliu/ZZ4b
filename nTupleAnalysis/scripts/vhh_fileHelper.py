def getCoupling(CV = "1_0", C2V = "1_0", C3 = "1_0"):
    coupling = "CV_" + CV + "_C2V_" + C2V + "_C3_" + C3
    files = []
    for V in ["Z", "W", "V"]:
        files.append(V + "HHTo4B_" + coupling + "_")
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

# ZHH 2017 C3:0_0 missing
#
# signals = signalFiles('CV:0_5,C2V:0_0,,C3:2_0,C2V:2_0,CV:1_5')
# signalDirs = []
# for signal in signals:
#     for file in signal:
#         if 'VHH' not in file:
#             for year in ['2017', '2018']:
#                 signalDirs.append(file + year + '/')
# xrdcpFiles('/store/user/jda102/condor/VHHSkims/', './', signalDirs, {'picoAOD_b0p60p3.root':'picoAOD.root'})