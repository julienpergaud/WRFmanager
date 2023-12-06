#! /usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys as sys
import f90nml as nList
import logging as logging
import os as os

import ConfigReader.ConfigFileFunction as cffunc
import Tools.TestRepFunction as repfunc
import Process.RunProcess as runfunc
import Tools.dateManager as datfunc

#test
# initialize logger
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('./run_Prepro.log')
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
    wpsDirRun=repfunc.creatRep(dirProject,'PREPRO',logger,force=dictConfig["eraseDir"])
except ValueError:
    sys.exit()        

dateBlocList=datfunc.dateRunManager(dictConfig,logger)






#Read and test Namelist
if os.path.isfile(dictConfig["namelistDir"]+'/'+'namelist.wps'):
    nml=nList.read(dictConfig["namelistDir"]+"/namelist.wps")
else:
    logger.error('namelist.wps does not exist in '+dictConfig["namelistDir"])
    logger.error('Prepro Manager stops')
    sys.exit()    

nbDomain=nml['share']['max_dom']
try:
    nameGeoTBLDir=nml['geogrid']['opt_geogrid_tbl_path']
except:
    nameGeoTBLDir='./'
else:
    if nameGeoTBLDir[len(nameGeoTBLDir)-1]!='/':
        nameGeoTBLDir=nameGeoTBLDir+'/'
# Patch namelist dates

for i in range(0,len(dateBlocList)-1):
    dateSList=[]
    dateEList=[]
    
    for j in range(0,nbDomain):
        dateSList.append(dateBlocList[i].strftime('%Y-%m-%d_%H:%M:%S'))
        dateEList.append(dateBlocList[i+1].strftime('%Y-%m-%d_%H:%M:%S'))
    nml['share']['start_date']=dateSList
    nml['share']['end_date']=dateEList 
    dateBegin=dateBlocList[i]
    dateEnd=dateBlocList[i+1]
    try:
        wpsDirBloc=repfunc.creatRep(wpsDirRun,'Bloc_'+str(i),logger,force=False)
    except ValueError:
        sys.exit()
    os.chdir(wpsDirBloc)

    nml.write(wpsDirBloc+"/namelist.wps",force=True)

    if dictConfig["WPSDir"]!=wpsDirBloc: 
        listFileWPSOri=os.listdir(dictConfig["WPSDir"])
        for row in listFileWPSOri:
            if 'namelist' not in row:
                if 'geogrid' not in row and 'metgrid' not in row:
                    err=subprocess.call('ln -s '+dictConfig["WPSDir"]+'/'+row, shell=True)
                else: 
                    err=subprocess.call('cp -r '+dictConfig["WPSDir"]+'/'+row+ ' ./', shell=True)
  



    # geogrid section
    idJobGeo=''
    if dictConfig["geogrid"]==True:
        try:
            if dictConfig["GeoTBLFile"]!='':
                try:
                    if os.path.isfile(nameGeoTBLDir+'./GEOGRID.TBL'):
                        err=subprocess.call('rm '+nameGeoTBLDir+'./GEOGRID.TBL', shell=True)
                    err=subprocess.call('ln -s '+dictConfig["GeoTBLFile"]+' '+nameGeoTBLDir+'GEOGRID.TBL', shell=True)
                except:
                    logger.error(dictConfig["GeoTBLFile"]+' is not a valid file')
                    logger.error('Prepro Manager stops')
                    sys.exit()
                    
            runfunc.CreateJobFile(dictConfig,'geogrid',i)
            idJobGeo=runfunc.RunProcess("qsub -terse ./geogrid_job")
            
        except OSError:
            logger.error( 'check if geogrid.exe is present')
            logger.error('Prepro Manager stops')
            sys.exit()

    



# ungrib section
    idJob=''
    idJobUngrib=runfunc.RunUngrib(dictConfig,logger,dateBegin,dateEnd,'',wpsDirBloc,i)
    if idJobUngrib!='':
        idJob=idJobUngrib 


  


#TAVGSFC et calc_ecmwf section
    nml=nList.read(wpsDirBloc+"/namelist.wps")
    if dictConfig["ungrib"]:
        if dictConfig["ungribSST"]==True:
            if dictConfig["ECsigma"]==True:
                nml['metgrid']['fg_name']=['FILE','SST_FILE','PRES']

            else:
                nml['metgrid']['fg_name']=['FILE','SST_FILE']
                
        else:
            if dictConfig["ECsigma"]==True:
                nml['metgrid']['fg_name']=['FILE','PRES']

            else:
                nml['metgrid']['fg_name']='FILE'
    
    
    elif dictConfig['dirIntermediateFile']!='':
        nml['metgrid']['fg_name']=dictConfig['prefixIntermediateFile']
        if dictConfig["ungribSST"]==True:
            nml['metgrid']['fg_name']=[dictConfig['prefixIntermediateFile'],'SST_FILE']
        elif dictConfig['dirIntermediateFile']!='':
            nml['metgrid']['fg_name']=[dictConfig['prefixIntermediateFile'],dictConfig['prefixIntermediateSSTFile']]

            
            
    nml['metgrid']['opt_output_from_metgrid_path']=dictConfig['dirMetFile']
    if dictConfig['TAVGSFC']:
        nml['metgrid']['constants_name']='TAVGSFC'
        
    nml.write(wpsDirBloc+"/namelist.metgrid",force=True)


    idJobECsigma=''
    if dictConfig['ECsigma']:
        try:
            err=subprocess.call("ln -s "+dictConfig['sigmaFile']+" ecmwf_coeffs", shell=True)
            runfunc.CreateJobFile(dictConfig,'ECMWF_PRES',i)
            nameJob=' ECMWF_PRES_job'
            if idJob!='':
                idJobECsigma=runfunc.SubmitJob(dictConfig,nameJob,[idJob])
            else:
                idJobECsigma=runfunc.SubmitJob(dictConfig,nameJob)

            
        except OSError:
            logger.error( 'check if calc_ecmwf_p.exe is present')
            logger.error( 'check if ecmwf_coeffs '+dictConfig['sigmaFile']+' is present')
            logger.error('Prepro Manager stops')
            sys.exit()        
        if idJobECsigma!='':
            idJob=idJobECsigma   
   
    idJobTavgSfc=''
    if dictConfig['TAVGSFC']:
        try:
            err=subprocess.call("ln -s ./util/avg_tsfc.exe", shell=True)
            runfunc.CreateJobFile(dictConfig,'TAVGSFC',i)
            nameJob='TAVGSFC_job '
            if idJob!='':
                idJobTavgSfc=runfunc.SubmitJob(dictConfig,nameJob,[idJob])
            else:
                idJobTavgSfc=runfunc.SubmitJob(dictConfig,nameJob)
            
        except OSError:
            logger.error( 'check if avg_tsfc.exe is present')
            logger.error('Prepro Manager stops')
            sys.exit()        
        if idJobTavgSfc!='':
            idJob=idJobTavgSfc   
            
# metgrid section
    runfunc.RunMetgrid(dictConfig,logger,idJob,wpsDirBloc,i,idJobGeo)
        
logger.removeHandler(hdlr)
hdlr.close()




















