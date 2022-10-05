# https://github.com/CoffeaTeam/lpcjobqueue
# curl -OL https://raw.githubusercontent.com/CoffeaTeam/lpcjobqueue/main/bootstrap.sh
# bash bootstrap.sh
# unset PYTHONPATH
# voms
# ./shell

# To use dask monitor in your browser, connect to your lpc interative node with:
# ssh -XY -L 8000:localhost:8787 <user>@cmslpc<number>.fnal.gov
# Then load "localhost:8000" on a browser on your computer

from distributed import Client
from lpcjobqueue import LPCCondorCluster


transfer_input_files = ['ZZ4b/nTupleAnalysis/scripts/coffea_analysis.py', 'ZZ4b/nTupleAnalysis/scripts/MultiClassifierSchema.py', 'ZZ4b/nTupleAnalysis/scripts/networks.py',
                        'nTupleAnalysis/baseClasses/data/BTagSF2016/btagging_legacy16_deepJet_itFit.json.gz',
                        'nTupleAnalysis/baseClasses/data/BTagSF2017/btagging_legacy17_deepJet.json.gz',
                        'nTupleAnalysis/baseClasses/data/BTagSF2018/btagging_legacy18_deepJet.json.gz',
                        'ZZ4b/nTupleAnalysis/pytorchModels/SvB_HCR_8_np753_seed0_lr0.01_epochs20_offset0_epoch20.pkl',
                        'ZZ4b/nTupleAnalysis/pytorchModels/SvB_HCR_8_np753_seed0_lr0.01_epochs20_offset1_epoch20.pkl',
                        'ZZ4b/nTupleAnalysis/pytorchModels/SvB_HCR_8_np753_seed0_lr0.01_epochs20_offset2_epoch20.pkl',
                    ]

# import torch
# torch.set_num_threads(1)
# torch.set_num_interop_threads(1)



if __name__ == '__main__':
    from coffea_analysis import *

    # print(torch.__config__.parallel_info())

    eos_base = 'root://cmseos.fnal.gov//store/user/pbryant/condor'
    nfs_base = '/uscms/home/bryantp/nobackup/ZZ4b'
    eos = True

    input_path  = f'{eos_base if eos else nfs_base}'
    output_path = f'{nfs_base}'

    metadata = {}
    fileset = {}
    years = ['2016', '2017', '2018']
    #years = ['2018']
    for year in years:
        datasets = [f'HH4b{year}']
        if year == '2016':
            datasets += [f'ZZ4b2016_preVFP',  f'ZH4b2016_preVFP',  f'ggZH4b2016_preVFP']
            datasets += [f'ZZ4b2016_postVFP', f'ZH4b2016_postVFP', f'ggZH4b2016_postVFP']
        else:
            datasets += [f'ZZ4b{year}', f'ZH4b{year}', f'ggZH4b{year}']
        
        for dataset in datasets:
            VFP = '_'+dataset.split('_')[-1] if 'VFP' in dataset else ''
            btagSF = btagSF_file(year+VFP, UL=False if 'HH4b' in dataset else True, conda_pack=True)
            metadata[dataset] = {'isMC'  : True,
                                 'xs'    : xsDictionary[dataset.replace(year+VFP,'')],
                                 'lumi'  : lumiDict[year+VFP],
                                 'year'  : year,
                                 'btagSF': btagSF,
                                 #'btagSF': btagSF_file(year+VFP, UL=False if 'HH4b' in dataset else True),
            }
            fileset[dataset] = {'files': [f'{input_path}/{dataset}/picoAOD.root',],
                                'metadata': metadata[dataset]}
            
            print(f'Dataset {dataset} with {len(fileset[dataset]["files"])} files')


    analysis_args = {'debug': False,
                     'JCM': 'ZZ4b/nTupleAnalysis/weights/dataRunII/jetCombinatoricModel_SB_00-00-02.txt',
                     'btagVariations': btagVariations(),
                     'SvB': 'ZZ4b/nTupleAnalysis/pytorchModels/SvB_HCR_8_np753_seed0_lr0.01_epochs20_offset*_epoch20.pkl',
    }


    cluster_args = {'transfer_input_files': transfer_input_files,
                    'shared_temp_directory': '/tmp',
                    'cores': 2,
                    'ship_env': False}

    cluster = LPCCondorCluster(**cluster_args)
    cluster.adapt(minimum=1, maximum=100)
    client = Client(cluster)
    # client = Client()

    print('Waiting for at least one worker...')
    client.wait_for_workers(1)


    executor_args = {
        'client': client,
        'savemetrics': True,
        'schema': NanoAODSchema,
        'align_clusters': False,
    }

    tstart = time.time()
    hists, metrics = processor.run_uproot_job(
        fileset,
        treename='Events',
        processor_instance=analysis(**analysis_args),
        executor=processor.dask_executor,
        executor_args=executor_args,
        chunksize=10_000,
        #maxchunks=4,
    )
    elapsed = time.time() - tstart

    # nEvent = sum([hists['nEvent'][dataset] for dataset in hists['nEvent'].keys()])
    nEvent = metrics['entries']
    processtime = metrics['processtime']
    print(f'\n{nEvent/elapsed:,.0f} events/s total ({nEvent}/{elapsed}, processtime {processtime})')

    with open('singularity/hists.pkl', 'wb') as hfile:
        pickle.dump(hists, hfile)

