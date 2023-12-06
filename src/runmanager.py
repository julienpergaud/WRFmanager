#! /usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys as sys
import f90nml as nList
import logging as logging
import os as os
import glob as glob

import ConfigReader.ConfigFileFunction as cffunc
import Tools.TestRepFunction as repfunc
import Process.RunProcess as runfunc
import Tools.dateManager as datefunc


# initialize logger
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('./run_Manager.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

# Parse Config file
config=cffunc.CreateConfigFile('./',logger)
Err=cffunc.ConfigFileControl(config,logger)
if not(Err):
    logger.error('Prepro Manager stops')
    sys.exit()
dictConfig=cffunc.ReadConfigFile(config,logger)

# Create directory
if not os.path.isdir(dictConfig["projectDir"]):
    logger.error('directory '+dictConfig["projectDir"]+' does not exist')
    sys.exit()
else:
    try:        
        dirProject=repfunc.creatRep(dictConfig["projectDir"],dictConfig["nameProject"],logger,force=False)
    except ValueError:
        sys.exit()
try:
    wrfDirRun=repfunc.creatRep(dirProject,'RUN',logger,force=dictConfig["eraseDir"])
except ValueError:
    sys.exit()   

dateBlocList=datefunc.dateRunManager(dictConfig,logger)






#Read and test Namelist
if os.path.isfile(dictConfig["namelistDir"]+'/'+'namelist.input'):
    nml=nList.read(dictConfig["namelistDir"]+"/namelist.input")
else:
    logger.error('namelist.input does not exist in '+dictConfig["namelistDir"])
    logger.error('Prepro Manager stops')
    sys.exit()   
    
if dictConfig['real']==False:      
    logger.info('------  Real --------')
    logger.info('option real defined to False')
    logger.info('real outputs must be contained in '+dictConfig['dirRealFile'])
    logger.info('same bloc division must be used')
    logger.info('Run Manager does not check if wrffdda or wrflowinp files must be present')
    logger.info('------  Real --------')
        
for i in range(0,len(dateBlocList)-1):
    
    nlistRun=datefunc.dateRealManager(dateBlocList[i],dateBlocList[i+1],dict(nml),logger,i,dictConfig)
    
    try:
        wrfDirBloc=repfunc.creatRep(wrfDirRun,'Bloc_'+str(i),logger,force=False)
    except ValueError:
        sys.exit()

    #Process namelisr for real
    os.chdir(wrfDirBloc)
    nbDomain=nlistRun['domains']['max_dom']
    nlistRun.write(wrfDirBloc+"/namelist.wrf",force=True)

    nlistRun['domains']['nproc_x']=-1
    nlistRun['domains']['nproc_y']=-1

    nlistRun.write(wrfDirBloc+"/namelist.real",force=True)

    

    if dictConfig["WRFDir"]!=wrfDirBloc: 
        listFileWPSOri=os.listdir(dictConfig["WRFDir"])
        for row in listFileWPSOri:
            if 'namelist' not in row:
                err=subprocess.call('ln -s '+dictConfig["WRFDir"]+'/'+row, shell=True)
    if dictConfig["dirGenMetFile"]!='':
        listFileWPSOri=runfunc.DateForMetgrid(dictConfig,dateBlocList[i],dateBlocList[i+1])
    else:
        repMetFile=dirProject+'/PREPRO/Bloc_'+str(i)+'/'+dictConfig['dirMetFile']
        listFileWPSOri=glob.glob(repMetFile+'/met_em*')
    for row in listFileWPSOri:
        subprocess.call('ln -s '+row, shell=True)

    if dictConfig["dirWrfFileToLink"]!='': 
        listFileWRFOther=os.listdir(dictConfig["dirWrfFileToLink"])
        for row in listFileWRFOther:
            err=subprocess.call('ln -s '+dictConfig["dirWrfFileToLink"]+'/'+row, shell=True)
            if err==1:
                os.remove('./'+row)
                err=subprocess.call('ln -s '+dictConfig["dirWrfFileToLink"]+'/'+row, shell=True)
    if dictConfig['real']==True:      
        try:
            runfunc.CreateJobFile(dictConfig,'real',i)
            idJobReal=runfunc.SubmitJob(dictConfig,' ./real_job')
        except OSError:
            logger.error( 'check if real.exe is present')
            logger.error('Run Manager stops')
            sys.exit()
    else:
        logger.info('------  Bloc_'+str(i)+' --------')
        logger.info('link all wrf inputs available in '+dictConfig['dirRealFile']+'/RUN/Bloc_'+str(i))
        listFileWRFInputs=glob.glob(dictConfig['dirRealFile']+'/RUN/Bloc_'+str(i)+'/wrfinput*')
        if listFileWRFInputs!=[]:
            for row in listFileWRFInputs:
                subprocess.call('ln -s '+row, shell=True)
        else:
            logger.error( 'no wrfinput in '+dictConfig['dirRealFile']+'/RUN/Bloc_'+str(i))

        listFileWRFInputs=glob.glob(dictConfig['dirRealFile']+'/RUN/Bloc_'+str(i)+'/wrffdda*')
        if listFileWRFInputs!=[]:
            for row in listFileWRFInputs:
                subprocess.call('ln -s '+row, shell=True)        
        listFileWRFInputs=glob.glob(dictConfig['dirRealFile']+'/RUN/Bloc_'+str(i)+'/wrflowinp*')
        if listFileWRFInputs!=[]:
            for row in listFileWRFInputs:
                subprocess.call('ln -s '+row, shell=True)           
        listFileWRFInputs=glob.glob(dictConfig['dirRealFile']+'/RUN/Bloc_'+str(i)+'/wrfbdy*')
        if listFileWRFInputs!=[]:
            for row in listFileWRFInputs:
                subprocess.call('ln -s '+row, shell=True)         
        else:
            logger.error( 'no wrfbdy in '+dictConfig['dirRealFile']+'/RUN/Bloc_'+str(i))
                 
    if dictConfig['wrf']==True:      

        try:
            runfunc.CreateJobFile(dictConfig,'wrf',i,dateBlocList[i],nbDomain)
            if dictConfig['real']==True:
                if i==0:
                    idJobWRF=runfunc.SubmitJob(dictConfig,' ./wrf_job',[idJobReal])
                else:                    
                    idJobWRF=runfunc.SubmitJob(dictConfig,' ./wrf_job',[idJobReal,idJobWRFtmp])
            else:
                if i==0:
                    idJobWRF=runfunc.SubmitJob(dictConfig,' ./wrf_job')
                else:
                    idJobWRF=runfunc.SubmitJob(dictConfig,' ./wrf_job',[idJobWRFtmp])
        except OSError:
            logger.error( 'check if real.exe is present')
            logger.error('Run Manager stops')
            sys.exit()
        idJobWRFtmp=idJobWRF
logger.removeHandler(hdlr)
hdlr.close()


