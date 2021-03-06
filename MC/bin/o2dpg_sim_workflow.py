#!/usr/bin/env python3

#
# A script producing a consistent MC->RECO->AOD workflow 
# It aims to handle the different MC possible configurations 
# It just creates a workflow.json txt file, to execute the workflow one must execute right after
#   ${O2DPG_ROOT}/MC/bin/o2_dpg_workflow_runner.py -f workflow.json 
# Execution examples:
#   ./o2dpg_sim_workflow.py -e TGeant3 -nb 0 -ns 2 -j 8 -tf 1 -mod "-m TPC" -proc "jets" -ptTrigMin 3.5 -ptHatBin 3 -trigger "external" -ini "\$O2DPG_ROOT/MC/config/PWGGAJE/ini/trigger_decay_gamma.ini" --embedding False 
#
#  ./o2dpg_sim_workflow.py -e TGeant3 -nb 0 -ns 2 -j 8 -tf 1 -mod "--skipModules ZDC" -proc "ccbar"  --embedding True 
# 

import argparse
from os import environ
import json
import array as arr

parser = argparse.ArgumentParser(description='Create a MC simulation workflow')

parser.add_argument('-ns',help='number of signal events / timeframe', default=20)
parser.add_argument('-gen',help='generator: pythia8, extgen', default='pythia8')
parser.add_argument('-proc',help='process type: dirgamma, jets, ccbar', default='')
parser.add_argument('-trigger',help='event selection: particle, external', default='')
parser.add_argument('-ini',help='generator init parameters file, for example: ${O2DPG_ROOT}/MC/config/PWGHF/ini/GeneratorHF.ini', default='')
parser.add_argument('-confKey',help='generator or trigger configuration key values, for example: GeneratorPythia8.config=pythia8.cfg', default='')

parser.add_argument('-eCMS',help='CMS energy', default=5200.0)
parser.add_argument('-col',help='collision sytem: pp, PbPb, pPb, Pbp, ...', default='pp')
parser.add_argument('-ptHatBin',help='pT hard bin number', default=-1)
parser.add_argument('-ptHatMin',help='pT hard minimum when no bin requested', default=0)
parser.add_argument('-ptHatMax',help='pT hard maximum when no bin requested', default=-1)
parser.add_argument('-ptTrigMin',help='generated pT trigger minimum', default=0)
parser.add_argument('-ptTrigMax',help='generated pT trigger maximum', default=-1)

parser.add_argument('--embedding',help='whether to embedd into background', default=False) 
parser.add_argument('-nb',help='number of background events / timeframe', default=20)
parser.add_argument('-genBkg',help='generator', default='pythia8hi')
parser.add_argument('-iniBkg',help='generator init parameters file', default='${O2DPG_ROOT}/MC/config/common/ini/basic.ini')

parser.add_argument('-e',help='simengine', default='TGeant4')
parser.add_argument('-tf',help='number of timeframes', default=2)
parser.add_argument('-j',help='number of workers (if applicable)', default=8)
parser.add_argument('-mod',help='Active modules', default='--skipModules ZDC')
parser.add_argument('-seed',help='random seed number', default=0)
parser.add_argument('-o',help='output workflow file', default='workflow.json')
parser.add_argument('--noIPC',help='disable shared memory in DPL') 
args = parser.parse_args()
print (args)

# make sure O2DPG + O2 is loaded
O2DPG_ROOT=environ.get('O2DPG_ROOT')
O2_ROOT=environ.get('O2_ROOT')

if O2DPG_ROOT == None: 
   print('Error: This needs O2DPG loaded')
#   exit(1)

if O2_ROOT == None: 
   print('Error: This needs O2 loaded')
#   exit(1)

# ----------- START WORKFLOW CONSTRUCTION ----------------------------- 

NTIMEFRAMES=int(args.tf)
NWORKERS=args.j
MODULES=args.mod #"--skipModules ZDC"
SIMENGINE=args.e

# add here other possible types

workflow={}
workflow['stages'] = []

taskcounter=0
def createTask(name='', needs=[], tf=-1, cwd='./'):
    global taskcounter
    taskcounter = taskcounter + 1
    return { 'name': name, 'cmd':'', 'needs': needs, 'resources': { 'cpu': -1 , 'mem': -1 }, 'timeframe' : tf, 'labels' : [], 'cwd' : cwd }

def getDPL_global_options():
   if args.noIPC!=None:
      return "-b --run --no-IPC"
   return "-b --run --shm-segment-size ${SHMSIZE:-50000000000} --session " + str(taskcounter)
   

doembedding=True if args.embedding=='True' or args.embedding==True else False

if doembedding:
    # ---- background transport task -------
    NBKGEVENTS=args.nb
    GENBKG=args.genBkg
    INIBKG=args.iniBkg
    BKGtask=createTask(name='bkgsim')
    BKGtask['cmd']='o2-sim -e ' + SIMENGINE + ' -j ' + str(NWORKERS) + ' -n ' + str(NBKGEVENTS) + ' -g  ' + str(GENBKG) +  str(MODULES) + ' -o bkg --configFile ' + str(INIBKG)
    workflow['stages'].append(BKGtask)

# loop over timeframes
for tf in range(1, NTIMEFRAMES + 1):
   timeframeworkdir='tf'+str(tf)

   # ----  transport task -------
   # function encapsulating the signal sim part
   # first argument is timeframe id
   RNDSEED=args.seed    # 0 means random seed !
   ECMS=args.eCMS
   NSIGEVENTS=args.ns
   GENERATOR=args.gen
   INIFILE=''
   if args.ini!= '':
      INIFILE=' --configFile ' + args.ini
   CONFKEY=''
   if args.confKey!= '':
      CONFKEY=' --configKeyValue ' + args.confKey
   PROCESS=args.proc
   TRIGGER=''
   if args.trigger != '':
      TRIGGER=' -t ' + args.trigger
   
   PTTRIGMIN=float(args.ptTrigMin)  
   PTTRIGMAX=float(args.ptTrigMax) 

   # Recover PTHATMIN and PTHATMAX from pre-defined array depending bin number PTHATBIN
   # or just the ones passed
   PTHATBIN=int(args.ptHatBin)  
   PTHATMIN=int(args.ptHatMin)  
   PTHATMAX=int(args.ptHatMax) 
   # I would move next lines to a external script, not sure how to do it (GCB)
   if PTHATBIN > -1:
           # gamma-jet 
      if   PROCESS == 'dirgamma': 
           low_edge = arr.array('l', [5,  11, 21, 36, 57, 84])
           hig_edge = arr.array('l', [11, 21, 36, 57, 84, -1])
           PTHATMIN=low_edge[PTHATBIN]
           PTHATMAX=hig_edge[PTHATBIN]
           # jet-jet
      elif PROCESS == 'jets': 
          # Biased jet-jet
          # Define the pt hat bin arrays and set bin depending threshold
           if   PTTRIGMIN == 3.5:
                low_edge = arr.array('l', [5, 7,  9, 12, 16, 21])
                hig_edge = arr.array('l', [7, 9, 12, 16, 21, -1])
                PTHATMIN=low_edge[PTHATBIN]
                PTHATMAX=hig_edge[PTHATBIN]
           elif PTTRIGMIN == 7:
                low_edge = arr.array('l', [ 8, 10, 14, 19, 26, 35, 48, 66])
                hig_edge = arr.array('l', [10, 14, 19, 26, 35, 48, 66, -1])
                PTHATMIN=low_edge[PTHATBIN]
                PTHATMAX=hig_edge[PTHATBIN]
           #unbiased
           else:
                low_edge = arr.array('l', [ 0, 5, 7,  9, 12, 16, 21, 28, 36, 45, 57, 70, 85,  99, 115, 132, 150, 169, 190, 212, 235])
                hig_edge = arr.array('l', [ 5, 7, 9, 12, 16, 21, 28, 36, 45, 57, 70, 85, 99, 115, 132, 150, 169, 190, 212, 235,  -1])
                PTHATMIN=low_edge[PTHATBIN]
                PTHATMAX=hig_edge[PTHATBIN]
      else:
           low_edge = arr.array('l', [ 0, 5, 7,  9, 12, 16, 21, 28, 36, 45, 57, 70, 85,  99, 115, 132, 150, 169, 190, 212, 235])
           hig_edge = arr.array('l', [ 5, 7, 9, 12, 16, 21, 28, 36, 45, 57, 70, 85, 99, 115, 132, 150, 169, 190, 212, 235,  -1])
           PTHATMIN=low_edge[PTHATBIN]
           PTHATMAX=hig_edge[PTHATBIN]
           
   # translate here collision type to PDG
   # not sure this is what we want to do (GCB)
   COLTYPE=args.col

   if COLTYPE == 'pp':
      PDGA=2212 # proton
      PDGB=2212 # proton

   if COLTYPE == 'PbPb':
      PDGA=2212 # Pb????
      PDGB=2212 # Pb????

   if COLTYPE == 'pPb':
      PDGA=2212 # proton
      PDGB=2212 # Pb????

   if COLTYPE == 'Pbp':
      PDGA=2212 # Pb????
      PDGB=2212 # proton

   # produce the signal configuration
   SGN_CONFIG_task=createTask(name='gensgnconf_'+str(tf), tf=tf, cwd=timeframeworkdir)
   if GENERATOR == 'pythia8':
      SGN_CONFIG_task['cmd'] = '${O2DPG_ROOT}/MC/config/common/pythia8/utils/mkpy8cfg.py \
                --output=pythia8_'+ str(tf) +'.cfg \
	              --seed='+str(RNDSEED)+' \
	              --idA='+str(PDGA)+' \
	              --idB='+str(PDGB)+' \
	              --eCM='+str(ECMS)+' \
	              --process='+str(PROCESS)+' \
	              --ptHatMin=' + str(PTHATMIN) + ' \
	              --ptHatMax=' + str(PTHATMAX)
      workflow['stages'].append(SGN_CONFIG_task) 
   # elif GENERATOR == 'extgen': what do we do if generator is not pythia8?
                   
   if doembedding:
       # link background files to current working dir for this timeframe
       LinkBKGtask=createTask(name='linkbkg_'+str(tf), needs=[BKGtask['name']], tf=tf, cwd=timeframeworkdir)
       LinkBKGtask['cmd']='ln -s ../bkg*.root .'
       workflow['stages'].append(LinkBKGtask) 

   # transport signals
   signalprefix='sgn_' + str(tf)
   signalneeds=[ SGN_CONFIG_task['name'] ]
   embeddinto= "--embedIntoFile bkg_Kine.root" if doembedding else ""
   if doembedding:
       signalneeds = signalneeds + [ BKGtask['name'], LinkBKGtask['name'] ]
   SGNtask=createTask(name='sgnsim_'+str(tf), needs=signalneeds, tf=tf, cwd='tf'+str(tf))
   #SGNtask['cmd']='o2-sim -e '+str(SIMENGINE) + ' ' + str(MODULES) + ' -n ' + str(NSIGEVENTS) +  ' -j ' + str(NWORKERS) + ' -g extgen \
   #    --configFile ${O2DPG_ROOT}/MC/config/PWGHF/ini/GeneratorHF.ini                    \
   #    --configKeyValues \"GeneratorPythia8.config=pythia8_'+ str(tf) +'.cfg\"'          \
   #    + ' -o ' + signalprefix + ' ' + embeddinto
   SGNtask['cmd']='o2-sim -e ' + str(SIMENGINE) + ' ' + str(MODULES) + ' -n ' + str(NSIGEVENTS) +  ' -j ' + str(NWORKERS) + ' -g ' + str(GENERATOR) + ' ' + str(TRIGGER)+ ' ' + str(CONFKEY) + ' ' + str(INIFILE) + ' -o ' + signalprefix + ' ' + embeddinto
   workflow['stages'].append(SGNtask)

   # some tasks further below still want geometry + grp in fixed names, so we provide it here
   # Alternatively, since we have timeframe isolation, we could just work with standard o2sim_ files
   LinkGRPFileTask=createTask(name='linkGRP_'+str(tf), needs=[SGNtask['name']], tf=tf, cwd=timeframeworkdir)
   LinkGRPFileTask['cmd']='ln -s ' + signalprefix + '_grp.root o2sim_grp.root ; ln -s ' + signalprefix + '_geometry.root o2sim_geometry.root'
   workflow['stages'].append(LinkGRPFileTask)


   CONTEXTFILE='collisioncontext.root'
 
   simsoption=' --sims ' + ('bkg,'+signalprefix if doembedding else signalprefix)
   TPCDigitask=createTask(name='tpcdigi_'+str(tf), needs=[SGNtask['name'], LinkGRPFileTask['name']], tf=tf, cwd=timeframeworkdir)
   TPCDigitask['cmd'] = 'o2-sim-digitizer-workflow ' + getDPL_global_options() + ' -n ' + str(args.ns) + simsoption + ' --onlyDet TPC --interactionRate 50000 --tpc-lanes ' + str(NWORKERS) + ' --outcontext ' + str(CONTEXTFILE)
   workflow['stages'].append(TPCDigitask)

   # The TRD digi task has a dependency on TPC only because of the digitization context (and because they both use CPU efficiently)
   # TODO: activate only if TRD present
   TRDDigitask=createTask(name='trddigi_'+str(tf), needs=[TPCDigitask['name']], tf=tf, cwd=timeframeworkdir)
   TRDDigitask['cmd'] = 'o2-sim-digitizer-workflow ' + getDPL_global_options() + ' -n ' + str(args.ns) + simsoption + ' --onlyDet TRD --interactionRate 50000 --configKeyValues \"TRDSimParams.digithreads=' + str(NWORKERS) + '\" --incontext ' + str(CONTEXTFILE)
   workflow['stages'].append(TRDDigitask)

   RESTDigitask=createTask(name='restdigi_'+str(tf), needs=[TPCDigitask['name'], LinkGRPFileTask['name']], tf=tf, cwd=timeframeworkdir)
   RESTDigitask['cmd'] = 'o2-sim-digitizer-workflow ' + getDPL_global_options() + ' -n ' + str(args.ns) + simsoption + ' --skipDet TRD,TPC --interactionRate 50000 --incontext ' + str(CONTEXTFILE)
   workflow['stages'].append(RESTDigitask)

   # -----------
   # reco
   # -----------

   # TODO: check value for MaxTimeBin; A large value had to be set tmp in order to avoid crashes bases on "exceeding timeframe limit"
   TPCRECOtask=createTask(name='tpcreco_'+str(tf), needs=[TPCDigitask['name']], tf=tf, cwd=timeframeworkdir)
   TPCRECOtask['cmd'] = 'o2-tpc-reco-workflow ' + getDPL_global_options() + ' --tpc-digit-reader "--infile tpcdigits.root" --input-type digits --output-type clusters,tracks,send-clusters-per-sector  --configKeyValues "GPU_global.continuousMaxTimeBin=100000;GPU_proc.ompThreads='+str(NWORKERS)+'"'
   workflow['stages'].append(TPCRECOtask)

   ITSRECOtask=createTask(name='itsreco_'+str(tf), needs=[RESTDigitask['name']], tf=tf, cwd=timeframeworkdir)
   ITSRECOtask['cmd'] = 'o2-its-reco-workflow --trackerCA --tracking-mode async ' + getDPL_global_options()
   workflow['stages'].append(ITSRECOtask)

   FT0RECOtask=createTask(name='ft0reco_'+str(tf), needs=[RESTDigitask['name']], tf=tf, cwd=timeframeworkdir)
   FT0RECOtask['cmd'] = 'o2-ft0-reco-workflow ' + getDPL_global_options()
   workflow['stages'].append(FT0RECOtask)

   ITSTPCMATCHtask=createTask(name='itstpcMatch_'+str(tf), needs=[TPCRECOtask['name'], ITSRECOtask['name']], tf=tf, cwd=timeframeworkdir)
   ITSTPCMATCHtask['cmd']= 'o2-tpcits-match-workflow ' + getDPL_global_options() + ' --tpc-track-reader \"tpctracks.root\" --tpc-native-cluster-reader \"--infile tpc-native-clusters.root\"'
   workflow['stages'].append(ITSTPCMATCHtask)

   # this can be combined with TRD digitization if benefical
   TRDTRAPtask = createTask(name='trdtrap_'+str(tf), needs=[TRDDigitask['name']], tf=tf, cwd=timeframeworkdir)
   TRDTRAPtask['cmd'] = 'o2-trd-trap-sim'
   workflow['stages'].append(TRDTRAPtask)

   TRDTRACKINGtask = createTask(name='trdreco_'+str(tf), needs=[TRDTRAPtask['name'], ITSTPCMATCHtask['name'], TPCRECOtask['name'], ITSRECOtask['name']], tf=tf, cwd=timeframeworkdir)
   TRDTRACKINGtask['cmd'] = 'o2-trd-global-tracking'
   workflow['stages'].append(TRDTRACKINGtask)

   TOFRECOtask = createTask(name='tofmatch_'+str(tf), needs=[ITSTPCMATCHtask['name'], RESTDigitask['name']], tf=tf, cwd=timeframeworkdir)
   TOFRECOtask['cmd'] = 'o2-tof-reco-workflow ' + getDPL_global_options()
   workflow['stages'].append(TOFRECOtask)

   PVFINDERtask = createTask(name='pvfinder_'+str(tf), needs=[ITSTPCMATCHtask['name'], FT0RECOtask['name']], tf=tf, cwd=timeframeworkdir)
   PVFINDERtask['cmd'] = 'o2-primary-vertexing-workflow ' + getDPL_global_options()
   workflow['stages'].append(PVFINDERtask)
 
  # -----------
  # produce AOD
  # -----------
  
  # enable later. It still has memory access problems 
  # taskwrapper aod_${tf}.log o2-aod-producer-workflow --aod-writer-keep dangling --aod-writer-resfile "AO2D" --aod-writer-resmode UPDATE --aod-timeframe-id ${tf} $gloOpt
   AODtask = createTask(name='aod_'+str(tf), needs=[PVFINDERtask['name'], TOFRECOtask['name'], TRDTRACKINGtask['name']], tf=tf, cwd=timeframeworkdir)
   AODtask['cmd'] = ' echo "Would do AOD (enable later)" '
   workflow['stages'].append(AODtask)

   # cleanup step for this timeframe (we cleanup disc space early so as to make possible checkpoint dumps smaller)
   CLEANUPtask = createTask(name='cleanup_'+str(tf), needs=[AODtask['name']], tf=tf, cwd=timeframeworkdir)
   CLEANUPtask['cmd'] = ' echo "Doing cleanup" '
   workflow['stages'].append(CLEANUPtask)


def trimString(cmd):
  return ' '.join(cmd.split())

# insert taskwrapper stuff
for s in workflow['stages']:
  s['cmd']='. ${O2_ROOT}/share/scripts/jobutils.sh; taskwrapper ' + s['name']+'.log \'' + s['cmd'] + '\''

# remove whitespaces etc
for s in workflow['stages']:
  s['cmd']=trimString(s['cmd'])


# write workflow to json
workflowfile=args.o
with open(workflowfile, 'w') as outfile:
    json.dump(workflow, outfile, indent=2)

exit (0)
