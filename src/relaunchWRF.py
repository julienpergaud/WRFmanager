#! /usr/bin/env python
# -*- coding: utf-8 -*-


import argparse as argP
import glob as glob
import os as os

import Process.RunProcess as runfunc

parser = argP.ArgumentParser(description='tool to relaunch qsub of wrf job launched by WRFmanager')
parser.add_argument('-b', '--bloc', type=int, default=0,help='integer defining the number of first bloc to relaunch')
parser.add_argument('-e', '--endbloc', type=int, default=-1,help='integer defining the number of last bloc to relaunch')
parser.add_argument('-d', '--directory', type=str, help='RUN directory created by WRFManager',required=True)
parser.add_argument('-c', '--centre', type=str, default="ccub", help='computing center ccub (default) or criann')


args = parser.parse_args()
numberBloc=args.bloc
numberBlocEnd=args.endbloc
runDir=args.directory
centre=args.centre

blocList=glob.glob(runDir+'/*')
nbBlocTotal=0
if numberBlocEnd==-1:
    for row in blocList:
        noBloc=int(row.split('_')[len(row.split('_'))-1])
        if noBloc>=nbBlocTotal:
            nbBlocTotal=noBloc
else:
    nbBlocTotal= numberBlocEnd   
firstJob=True


for i in range(numberBloc,nbBlocTotal+1):
    os.chdir(runDir+'/Bloc_'+str(i))
    dictConfig={'subjob':centre}
    if firstJob:
        idJobWRF=runfunc.SubmitJob(dictConfig,'wrf_job')
    else:
        idJobWRF=runfunc.SubmitJob(dictConfig,'wrf_job',[idJobWRF])                 
    
        
    firstJob=False
 
        
        
