#!/usr/bin/env python
#
# Scan through a digital rf recording
#
import numpy as n
import chirp_det as c
import chirp_config as cc
import digital_rf as drf
from mpi4py import MPI
import time
import sys
import traceback

comm=MPI.COMM_WORLD
size=comm.Get_size()
rank=comm.Get_rank()

def scan_for_chirps(conf,cfb,block0=None):
#    drf.recreate_properties_file("/mnt/ramdisk/hf25")
    d=drf.DigitalRFReader(conf.data_dir)
    b0=d.get_bounds(conf.channel0)
    b1=d.get_bounds(conf.channel1)

    if block0 == None:
        block0_ch0=int(n.ceil(b0[0]/(conf.n_samples_per_block*conf.step)))
        block0_ch1=int(n.ceil(b1[0]/(conf.n_samples_per_block*conf.step)))

    block1_ch0=int(n.floor(b0[1]/(conf.n_samples_per_block*conf.step)))
    block1_ch1=int(n.floor(b1[1]/(conf.n_samples_per_block*conf.step)))
    
    # mpi scan through dataset
    for block_idx in range(block0,block1):
        print('block_idx: %i' % block_idx)
        if block_idx%size == rank:
            # this is my block!
            try:
                cput0=time.time()
                # we may skip over data (step > 1) to speed up detection
                i0=block_idx*conf.n_samples_per_block*conf.step
                #            i0=block_idx*conf.n_samples_per_block*conf.step + idx0
                # read vector from recording
                z=d.read_vector_c81d(i0,conf.n_samples_per_block,conf.channel0)
                snrs,chirp_rates,f0s=cfb.seek(z,i0)
                cput1=time.time()
                analysis_time=(conf.n_samples_per_block*conf.step)/conf.sample_rate
                print("%d/%d Analyzing %s speed %1.2f * realtime"%( rank,
                                                                    size,
                                                                    c.unix2datestr(i0/conf.sample_rate),
                                                                    size*analysis_time/(cput1-cput0) ))
            except:
                print("error")
                traceback.print_exc()
    return(block1)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        conf=cc.chirp_config(sys.argv[1])
    else:
        conf=cc.chirp_config()
        
    cfb=c.chirp_matched_filter_bank(conf)
        
    if not conf.realtime:
        scan_for_chirps(conf,cfb)
    else:
        block1=None
        while True:
            block1=scan_for_chirps(conf,cfb,block1)
            time.sleep(0.001)
