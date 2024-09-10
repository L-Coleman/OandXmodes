#!/usr/bin/env python3
import matplotlib
matplotlib.use('Agg')
import numpy as n
import matplotlib.pyplot as plt
import glob
import h5py
import scipy.constants as c
import chirp_config as cc
import chirp_det as cd
import sys
import os
import os.path
import time
import traceback
import re

def kill(conf):
    exists = os.path.isfile(conf.kill_path)
    return exists

def plot_ionogram(conf,f,normalize_by_frequency=True):
    ho=h5py.File(f,"r")
    t0=float(n.copy(ho[("t0")]))
    p_ch=n.copy(ho[("p_ch")])
    if not "id" in ho.keys():
        return
    cid=int(n.copy(ho[("id")]))  # ionosonde id
    
    img_fname="%s/%s/lfm_ionogram-%03d-%1.2f.png"%(conf.output_dir,cd.unix2dirname(t0),cid,t0)
    if os.path.exists(img_fname):
        print("Ionogram plot %s already exists. Skipping"%(img_fname))
        ho.close()
        return
    
    print("Plotting %s rate %1.2f (kHz/s) t0 %1.5f (unix)"%(f,float(n.copy(ho[("rate")]))/1e3,float(n.copy(ho[("t0")]))))
    #Spo=n.copy(n.array(ho[("Spo")],dtype=n.float64))          # ionogram frequency-range
    #Spx=n.copy(n.array(ho[("Spx")],dtype=n.float64))
    #SSp=n.copy(n.array(ho[("SSp")],dtype=n.float64))
    #SSs=n.copy(n.array(ho[("SSs")],dtype=n.float64))    
    Sp=n.copy(n.array(ho[("Sp")],dtype=n.float64))          # ionogram frequency-range
    Ss=n.copy(n.array(ho[("Ss")],dtype=n.float64))
    phase_diff=n.copy(n.array(ho[("phase_diff")],dtype=n.float64))
    pfreqs=n.copy(ho[("pfreqs")])
    sfreqs=n.copy(ho[("sfreqs")])  # frequency bins
    ranges=n.copy(ho[("ranges")])  # range gates

    #Sp= (Spo+SSp)
    #Ss= (Spx+SSs)
    if normalize_by_frequency:
        for i in range(Sp.shape[0]):
            noise=n.nanmedian(Sp[i,:])
            Sp[i,:]=(Sp[i,:]-noise)/noise
        Sp[Sp<=0.0]=1e-3
        for j in range(Ss.shape[0]):
            noise=n.nanmedian(Ss[j,:])
            Ss[j,:]=(Ss[j,:]-noise)/noise
        Ss[Ss<=0.0]=1e-3
          

    #max_range_idx=[n.argmax(n.max(Sp,axis=0)),n.argmax(n.max(Ss,axis=0))]
    phase_diff = n.transpose(phase_diff *180/n.pi +180)
    
    dBp=n.transpose(10.0*n.log10(Sp))
    dBs=n.transpose(10.0*n.log10(Ss))
    if normalize_by_frequency == False:
        dBp=dBp-n.nanmedian(dBp)
        dBs=dBs-n.nanmedian(dBs)

    dBp[n.isnan(dBp)]=0.0
    dBs[n.isnan(dBs)]=0.0
    dBp[n.isfinite(dBp)!=True]=0.0    
    dBs[n.isfinite(dBs)!=True]=0.0  
    tracesonly= (dBp<=9.9) & (dBs<=9.9)
    phase_diff[tracesonly] = n.nan 
    # assume that t0 is at the start of a standard unix second
    # therefore, the propagation time is anything added to a full second

    dt=(t0-n.floor(t0))
    dr=dt*c.c/1e3
    # converted to one-way travel time
    range_gates=dr+ranges/1e3
    #r0=range_gates[max_range_idx]
    
    fig,ax=plt.subplots(2,2,figsize=[14,10])
    a=ax[0,0].pcolormesh(pfreqs/1e6,range_gates,dBp,vmin=-3,vmax=30.0,cmap="inferno")
    fig.colorbar(a,ax=ax[0,0],label="SNR (dB)")

    b=ax[0,1].pcolormesh(sfreqs/1e6,range_gates,dBs,vmin=-3,vmax=30.0,cmap="inferno")
    fig.colorbar(b,ax=ax[0,1],label="SNR (dB)")

    d=ax[1,0].pcolormesh(sfreqs/1e6,range_gates,phase_diff,cmap="seismic")
    fig.colorbar(d,ax=ax[1,0],label="phase shift (deg)")
    
    counts, bins = n.histogram(phase_diff[n.isfinite(phase_diff)],bins=40)
    
    e=ax[1,1].plot(bins[:-1], counts, 'o--', color='k', alpha=0.3)
    #cb.set_label("SNR (dB)")
    fig.suptitle("Chirp-rate %1.2f kHz/s t0=%1.5f (unix s)\n%s %s (UTC)"%(float(n.copy(ho[("rate")]))/1e3,float(n.copy(ho[("t0")])),conf.station_name,cd.unix2datestr(float(n.copy(ho[("t0")])))),
                 y=0.92)
    ax[0,0].set_xlabel("Frequency (MHz)")
    ax[0,0].set_ylabel("One-way range offset (km)")
    ax[0,1].set_xlabel("Frequency (MHz)")
    ax[0,1].set_ylabel("One-way range offset (km)")
    ax[1,0].set_ylabel("One-way range offset (km)")
    ax[1,0].set_xlabel("Frequency (MHz)")
    ax[1,1].set_xlabel("Phase (deg)")
    ax[1,1].set_ylabel("Pixel Count")
    #if conf.manual_range_extent:
    #    plt.ylim([conf.min_range/1e3,conf.max_range/1e3])
    #else:
    #    plt.ylim([dr-conf.max_range_extent/1e3,dr+conf.max_range_extent/1e3])
        
#    plt.ylim([dr-1000.0,dr+1000.0])
    #if conf.manual_freq_extent:
    #    plt.xlim([conf.min_freq/1e6,conf.max_freq/1e6])
    #else:
    #    plt.xlim([0,conf.maximum_analysis_frequency/1e6])
    #plt.tight_layout()
    plt.savefig(img_fname)
    fig.clf()
    plt.clf()
    plt.close("all")
    import gc
    gc.collect()
    ho.close()
    sys.stdout.flush()
    if conf.copy_to_server:
        os.system("rsync -av %s %s/latest_%s.png"%(img_fname,conf.copy_destination,conf.station_name))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        conf=cc.chirp_config(sys.argv[1])
    else:
        conf=cc.chirp_config()

    if conf.realtime:
        while True:
            if kill(conf):
                print("kill.txt found, stopping plot_ionograms.py")
                sys.exit(0)
            else:
                fl=glob.glob("%s/*/lfm*.h5"%(conf.output_dir))
                fl.sort()
                t_now=time.time()
                # avoid last file to make sure we don't read and write simultaneously
                for f in fl[0:(len(fl)-1)]:
                    try:
                        t_file=float(re.search(".*-(1............).h5",f).group(1))
                        # new enough file
                        if t_now-t_file < 48*3600.0:
                            plot_ionogram(conf,f)
                    
                    except:
                        print("error with %s"%(f))
                        print(traceback.format_exc())
                time.sleep(10)
    else:
        fl=glob.glob("%s/*/lfm*.h5"%(conf.output_dir))
        for f in fl:
            try:
                plot_ionogram(conf,f)
            except:
                print("error with %s"%(f))
                print(traceback.format_exc())

                
            

