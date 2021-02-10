
import f90nml as nList
import os as os
import sys as sys
import Tools.TestRepFunction as repfunc
import shlex as shlex
import subprocess as subprocess
import datetime as dtime
import glob
import re

def RunUngrib(dictConfig,logger,dateBegin,dateEnd,idJobGeo,wpsDirRun,nbBloc):
    
    idJob=''
    idJobSST=''
    if dictConfig["ungrib"] or dictConfig["ungribSST"]:
        filesToLink=DateForUngrib(dictConfig,dateBegin,dateEnd)
        strListFile=''
        for row in sorted(filesToLink):
            strListFile=strListFile+' '+row
        try:
            err=subprocess.call("./link_grib.csh "+strListFile, shell=True)
        except:
            logger.error( 'check if link_grib.csh is present')
            logger.error('Prepro Manager stops')
            sys.exit()
    if dictConfig['dirIntermediateFile']!='' and dictConfig["ungrib"]==False:
        filesToLink=DateForPFile(dictConfig,dateBegin,dateEnd)
        if filesToLink!=[]:
            for row in filesToLink:
                subprocess.call('ln -s '+row, shell=True)
            idJob=idJobGeo
        else:
            logger.error( 'no PFILES to link')
            logger.error('Prepro Manager stops')
            sys.exit()           
            
    if dictConfig["ungrib"]:

    
        if dictConfig['vtableFile']!='Vtable':
            if os.path.isfile('./Vtable') and os.path.isfile(dictConfig['vtableFile']):
                err=subprocess.call('rm -f Vtable',shell=True)
                err=subprocess.call("cp "+dictConfig['vtableFile'] +" Vtable.ungrib", shell=True)
            else:
                if os.path.isfile(dictConfig['vtableFile']):
                    err=subprocess.call("cp "+dictConfig['vtableFile'] +" Vtable.ungrib", shell=True)
                else:
                    logger.warning(dictConfig['vtableFile']+' does not exist')
                    logger.warning('try to use local Vtable if exists')
         
                    
        nml=nList.read(wpsDirRun+"/namelist.wps")
        nml['ungrib']['prefix']='FILE'
        nml.write(wpsDirRun+"/namelist.ungrib",force=True)
        nameJob=' ./ungrib_job'

        idJob=''
        try:
            CreateJobFile(dictConfig,'ungrib',nbBloc)

            if idJobGeo != '': 
                idJob=SubmitJob(dictConfig,nameJob,[idJobGeo])
            else:
                idJob=SubmitJob(dictConfig,nameJob)


        except OSError:
            logger.error( 'check if ungrib.exe is present')
            logger.error('Prepro Manager stops')
            sys.exit()


    if dictConfig["ungribSST"]==True:
        if dictConfig['vtableSST']!='Vtable':
            if os.path.isfile('./Vtable') and os.path.isfile(dictConfig['vtableSST']):
                err=subprocess.call('rm -f Vtable',shell=True)
                err=subprocess.call("ln -s "+dictConfig['vtableSST'] +" Vtable.SST", shell=True)
            else:
                if os.path.isfile(dictConfig['vtableSST']):
                    err=subprocess.call("ln -s "+dictConfig['vtableSST'] +" Vtable.SST", shell=True)
                else:
                    logger.warning(dictConfig['vtableSST']+' does not exist')
                    logger.warning('try to use local Vtable if exists')


        nml=nList.read(wpsDirRun+"/namelist.wps")
        nml['ungrib']['prefix']='SST_FILE'
        nml.write(wpsDirRun+"/namelist.ungribSST",force=True)        
        idJobSST=''
        nameJob=' ./ungribSST_job'
        try:
            CreateJobFile(dictConfig,'ungribSST',nbBloc)
            if dictConfig["ungrib"]:
                if idJobGeo!='':
                    idJobSST=SubmitJob(dictConfig,nameJob,[idJob,idJobGeo])
                else:                    
                    idJobSST=SubmitJob(dictConfig,nameJob,[idJob])

            else:
                if idJobGeo!='':
                    idJobSST=SubmitJob(dictConfig,nameJob,[idJobGeo])
                else:                    
                    idJobSST=SubmitJob(dictConfig,nameJob)

        except OSError:
            logger.error( 'check if ungrib.exe is present')
            logger.error('Prepro Manager stops')
            sys.exit()
      
        idJob=idJobSST
        
    return idJob

def RunMetgrid(dictConfig,logger,idJob,wpsDirRun,nbBloc,idJobGeo=''):
    
 
    repfunc.creatRep(wpsDirRun,dictConfig['dirMetFile'],logger='',force=False)
    nameJob='./metgrid_job '
    try:
        
        if dictConfig["MetTBLFile"]!='':
            try:
                if os.path.isfile("metgrid/"+'./METGRID.TBL'):
                    err=subprocess.call('rm '+"metgrid/"+'./METGRID.TBL', shell=True)
                err=subprocess.call('ln -s '+dictConfig["MetTBLFile"]+' '+"metgrid/"+'METGRID.TBL', shell=True)
            except:
                logger.error(dictConfig["MetTBLFile"]+' is not a valid file')
                logger.error('Prepro Manager stops')
                sys.exit()
        CreateJobFile(dictConfig,'metgrid',nbBloc)
        if idJob!='':
            if idJobGeo!='':
                idFile=SubmitJob(dictConfig,nameJob,[idJob,idJobGeo])
            else:
                idFile=SubmitJob(dictConfig,nameJob,[idJob])
                
        else:
            if idJobGeo!='':
                idFile=SubmitJob(dictConfig,nameJob,[idJobGeo])
            else:
                idFile=SubmitJob(dictConfig,nameJob)
    except OSError:
        logger.error( 'check if metgrid.exe is present')
        logger.error('Prepro Manager stops')
        sys.exit()
  

def CreateJobFile(dictConfig,tool,blocNumber=0,dateBegin=dtime.datetime(1970,1,1,0,0,0),nbDomain=0):
    fileJob=open('./'+tool+'_job','w')

    if dictConfig['subjob']=="ccub":
        fileJob.write('#!/bin/ksh \n')
        if tool!='wrf' and tool != 'real':
            fileJob.write('#$ -q batch\n')
        elif dictConfig["binding"]== False:
            if dictConfig["madchinebind"]=='':
                fileJob.write('#$ -q batch\n')
            else:
                fileJob.write('#$ -q batch@'+dictConfig["madchinebind"]+'*\n')
            fileJob.write('#$ -l excl=true'+'\n')
    
        else:
            fileJob.write('#$ -q batch@'+dictConfig["madchinebind"]+'*\n')
            fileJob.write('#$ -l excl=true'+'\n')
           
        
        fileJob.write('#$ -N '+tool+'_'+dictConfig['nameProject']+'_'+str(blocNumber)+'\n')
        
        if tool=='geogrid':
            fileJob.write('geogrid.exe \n')
        elif tool == 'ungrib':
            fileJob.write('cp -f Vtable.ungrib Vtable \n')
            fileJob.write('cp -f namelist.ungrib namelist.wps \n')
            fileJob.write('ungrib.exe \n')
        elif tool == 'ungribSST':
            fileJob.write('cp -f Vtable.SST Vtable \n')
            fileJob.write('cp -f namelist.ungribSST namelist.wps \n')
            fileJob.write('ungrib.exe \n')
        elif tool == 'metgrid':
            fileJob.write('cp -f namelist.metgrid namelist.wps \n')
            fileJob.write('metgrid.exe \n') 
        elif tool == 'TAVGSFC':
            fileJob.write('cp -f namelist.metgrid namelist.wps \n')
            fileJob.write('avg_tsfc.exe \n')
        elif tool == 'ECMWF_PRES':
            fileJob.write('cp -f namelist.metgrid namelist.wps \n')
            fileJob.write('./util/calc_ecmwf_p.exe \n')
        elif tool == 'real':
            fileJob.write('#$ -pe dmp* '+str(dictConfig["nbprocReal"])+'\n')
            if dictConfig["nodededic"]!= '':
                fileJob.write(dictConfig["nodededic"]+' \n')
            if dictConfig["binding"]== False:
                fileJob.write('mpiib real.exe \n') 
            else:
                fileJob.write('mpirun --mca mpi_paffinity_alone 1 real.exe   \n')
    
                
        elif tool == 'wrf':

    
            
            fileJob.write('#$ -pe dmp* '+str(dictConfig["nbproc"])+'\n')
            if dictConfig["nodededic"]!= '':
                if dictConfig["nodededic"]=="amd":
                    fileJob.write('#$ -l vendor='+dictConfig["nodededic"]+' \n')
                else:
                    fileJob.write('#$ -l vendor='+dictConfig["nodededic"]+' \n')
                
            if blocNumber!=0:
                for i in range(1,nbDomain+1):
                    fileNameGen='wrfrst_d0'+str(i)+'_'+dateBegin.strftime('%Y-%m-%d_%H:%M:%S')        
                    fileNameGen='../Bloc_'+str(blocNumber-1)+'/'+fileNameGen
                    fileJob.write('ln -s '+fileNameGen+'\n') 
            if dictConfig["binding"]== False:
                if dictConfig["nodededic"]=="amd":
                    fileJob.write('mpirun -np '+str(dictConfig["nbproc"])+'  wrf.exe \n') 
                else:
                    fileJob.write('mpiib wrf.exe \n') 

            else:
                fileJob.write('mpirun --mca mpi_paffinity_alone 1 wrf.exe   \n')
    elif dictConfig['subjob']=="criann":
        fileJob.write('#!/bin/bash \n')
        fileJob.write('#SBATCH --exclusive \n')

        if tool!='wrf' and tool != 'real':
            fileJob.write('#SBATCH --partition court\n')
        elif  dictConfig["madchinebind"]=='':
            fileJob.write('#SBATCH --partition court\n')
        else:
            fileJob.write('#SBATCH --partition '+dictConfig["madchinebind"]+'\n')
           
        
        fileJob.write('#SBATCH -J '+tool+'_'+dictConfig['nameProject']+'_'+str(blocNumber)+'\n')
        
        if tool=='geogrid':
            fileJob.write('srun -n 1 geogrid.exe \n')
        elif tool == 'ungrib':
            fileJob.write('cp -f Vtable.ungrib Vtable \n')
            fileJob.write('cp -f namelist.ungrib namelist.wps \n')
            fileJob.write('srun -n 1 ungrib.exe \n')
        elif tool == 'ungribSST':
            fileJob.write('cp -f Vtable.SST Vtable \n')
            fileJob.write('cp -f namelist.ungribSST namelist.wps \n')
            fileJob.write('srun -n 1 ungrib.exe \n')
        elif tool == 'metgrid':
            fileJob.write('cp -f namelist.metgrid namelist.wps \n')
            fileJob.write('srun -n 1 metgrid.exe \n') 
        elif tool == 'TAVGSFC':
            fileJob.write('cp -f namelist.metgrid namelist.wps \n')
            fileJob.write('srun -n 1 avg_tsfc.exe \n')
        elif tool == 'ECMWF_PRES':
            fileJob.write('cp -f namelist.metgrid namelist.wps \n')
            fileJob.write('srun -n 1 ./util/calc_ecmwf_p.exe \n')
        elif tool == 'real':
            fileJob.write('#SBATCH --ntasks '+str(dictConfig["nbprocReal"])+'\n')
            fileJob.write('srun real.exe   \n')
    
                
        elif tool == 'wrf':
            fileJob.write('#SBATCH --ntasks '+str(dictConfig["nbproc"])+'\n')

            if blocNumber!=0:
                for i in range(1,nbDomain+1):
                    fileNameGen='wrfrst_d0'+str(i)+'_'+dateBegin.strftime('%Y-%m-%d_%H:%M:%S')        
                    fileNameGen='../Bloc_'+str(blocNumber-1)+'/'+fileNameGen
                    fileJob.write('ln -s '+fileNameGen+'\n') 
   
            
            fileJob.write('srun wrf.exe   \n')
        

    fileJob.close
    
def SubmitJob(dictConfig,nameJob,idJobList=[]):
    if dictConfig['subjob']=='ccub':
        commandLine='qsub -terse '
        if idJobList!=[]:
            commandLine=commandLine+'-hold_jid  '
            i=0
            for row in idJobList:
                if i==len(idJobList)-1:
                    commandLine=commandLine+str(row)
                else:
                    commandLine=commandLine+str(row)+','
                i=i+1
        commandLine=commandLine+' '+nameJob
        idJob=RunProcess(commandLine)

    elif dictConfig['subjob']=='criann':
        commandLine='sbatch '
        if idJobList!=[]:
            commandLine=commandLine+'--dependency=afterany:'
            i=0
            for row in idJobList:
                if i==len(idJobList)-1:
                    commandLine=commandLine+str(row)
                else:
                    commandLine=commandLine+str(row)+':'
                i=i+1
        commandLine=commandLine+' '+nameJob
        idJob=RunProcess(commandLine)
        idJob=idJob.split(' ')[3]      
        
    
    
    return idJob

def RunProcess(commandLine):    
    args=shlex.split(commandLine)
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    out=p.stdout.read()
    outmp=out.decode().split('\n')

    return outmp[0]


def DateForUngrib(dictConfig,dateBegin,dateEnd):
    
    listfile=[]
    listyear=[]
    listGribFile=glob.glob(dictConfig['dirGribFile']+"/"+dictConfig['prefixGriFile']+"*")
    yearBegin=dateBegin.year
    yearEnd=dateEnd.year
    listNameGen=[]
    for row in listGribFile:
        res = re.search("("+dictConfig['prefixGriFile']+".*?)(\d{4})[-_]{0,1}(\d{0,2})",row)
        year = int(res.group(2))
        nameGen=res.group(1)
        if year>=yearBegin and year <= yearEnd:
            if year not in listyear:
                listyear.append(year) 
            if nameGen not in listNameGen:
                listNameGen.append(nameGen)
    for year in listyear:
        for nameGen in listNameGen:
            listfile.append(dictConfig['dirGribFile']+"/"+nameGen+str(year)+"*")
  
    return listfile

def DateForMetgrid(dictConfig,dateBegin,dateEnd):
    
    listfile=[]
    listGribFile=glob.glob(dictConfig['dirGenMetFile']+"/"+"met_em*")


    for row in listGribFile:
        res = re.search("(\d{4})[-](\d{2})[-](\d{2})[_](\d{2})[:](\d{2})[:](\d{2})",row)
        year = int(res.group(1))
        month=int(res.group(2))
        day=int(res.group(3))
        hour = int(res.group(4))
        datefile=dtime.datetime(year,month, day,hour)
        if datefile>=dateBegin and datefile <= dateEnd:
            listfile.append(row)

        
        
    return listfile

def DateForPFile(dictConfig,dateBegin,dateEnd):
    
    listfile=[]
    listGribFile=glob.glob(dictConfig['dirIntermediateFile']+"/*/"+dictConfig['prefixIntermediateFile']+"*")

    for row in listGribFile:
        res = re.search(".*(\d{4})[-_]{0,1}(\d{0,2})[-_]{0,1}(\d{0,2})",row)
        year = int(res.group(1))
        month=int(res.group(2))
        day=int(res.group(3))
        datefile=dtime.datetime(year,month, day)

        if datefile>=dateBegin and datefile <= dateEnd:
            listfile.append(row)

        
        
    return listfile
