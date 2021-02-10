##@package src.ConfigReader.ConfigFileFunction
##@brief Function for reading the config file of TDS extraction tool and control it.
##@author J. Pergaud
##@date 20/03/2012
##@version 1.0

import sys as sys
import configparser as cp
import re
import datetime as dtime
import re as re

# Constants

##@param rep directory where config.ini file and default.cfg file are
##@brief Read config.ini file and default.cfg file and merge both.
##@return a configparser object
def CreateConfigFile(rep,logger):

    config = cp.ConfigParser()


    try:
        config.readfp(open(rep+'config.ini'))
    except IOError:
        logger.warning('Cannot open config.ini file')
        logger.warning( sys.exc_info()[1])
        sys.exit()
    except cp.ParsingError:
        logger.warning( 'Problem Parsing')
        logger.warning( sys.exc_info()[1])
        sys.exit()
       
    return config


##@param config a configparser object
##@brief Verify the entries in the config file. 
##This function can only stop the code or modify some option values  with default values
##@return Err a boolean True with no problem, False if not
def ConfigFileControl(config,logger):
    # Constants
    Err=True

    try:
        config.items("general")
        Err=Err and ControlOptionSection(config,"general",logger)
    except:
        logger.error( 'Section general is not present or not complete in config_file')
        Err=False
        return Err    
    try:
        config.items("prepro")
        Err=Err and ControlOptionSection(config,"prepro",logger)
    except:
        logger.error( 'Section prepro is not present or not complete in config_file')
        Err=False
        return Err  
    try:
        config.items("run")
        Err=Err and ControlOptionSection(config,"prepro",logger)
    except:
        logger.error( 'Section prepro is not present or not complete in config_file')
        Err=False
        return Err  
            
    
    
    return Err    
    
##@param config : a configparser object
##@param Section : a section name of the config file in which the options must be controlled 
##@brief Verify the options for the different section. 
##This function can only stop the code or modify some option values  with default values
##@return Err a boolean True with no problem, False if not
def ControlOptionSection(config,section,logger):   
      
    if section=='general' :
        listOfNeededOption = ['dateBegin','dateEnd',  \
                                'WPSDir','WRFDIR'] 
    if section=='prepro' :
        listOfNeededOption = ['prefixGribFile','dirGribFile']
        

    Err=True
    for element in listOfNeededOption:
        try:
            config.get(section,element)
        except cp.NoOptionError:
            logger.error( 'Section '+section+' option '+element+' is not present in config_file')
            Err=Err and False
    return Err



##@param config : a configparser object
##@brief Read, save and control option values. Create a config.output file summarize the chosen options. 
##@return dictConfig : a dictionary containing all the values of config.output file
def ReadConfigFile(config,logger):
    dictConfig={}

    # General section 
    dictConfig["dateBegin"]=TestOptionDate(config,'general','datebegin',logger)
    dictConfig["dateEnd"]=TestOptionDate(config,'general','dateend',logger)
       
    try:
        dictConfig["nameProject"]=config.get('general','nameProject')
    except:
        logger.warning( 'in section general nameProject is not defined')
        logger.warning( 'in section general nameProject is forced to TEST')        
        dictConfig["nameProject"]='TEST'
    try:
        dictConfig["DayByBloc"]=config.getint('general','DayByBloc')
    except:
        logger.warning( 'in section general DayByBloc is not defined or not well defined')
        logger.warning( 'DayByBloc must be an integer forced to 1461 (4 years)')        
        dictConfig["DayByBloc"]=1461
    
    dictConfig["WPSDir"]=config.get('general','WPSDir')
    dictConfig["WRFDir"]=config.get('general','WRFDir')

    try:
        dictConfig["namelistDir"]=config.get('general','namelistDir')
    except:
        logger.warning( 'in section general namelistDir is not defined')
        logger.warning( 'namelistDir forced to .')
        dictConfig["namelistDir"]='./'

    try:
        dictConfig["projectDir"]=config.get('general','projectDir')
    except:
        logger.warning( 'in section general projectDir is not defined')
        logger.warning( 'projectDir forced to .')
        dictConfig["projectDir"]='./'

    try:
        dictConfig["calendar"]=config.get('general','calendar')
    except:
        logger.warning( 'in section general calendar is not defined')
        logger.warning( 'calendar forced to gregorian')
        dictConfig["calendar"]='gregorian'
        
    try:
        dictConfig["eraseDir"]=TestOptionBoolean(config,'general','eraseDir',logger)
    except:
        logger.warning( 'in section general eraseDir is not defined or not well defined')
        logger.warning( 'eraseDir must be a boolean: forced to False')
        dictConfig["eraseDir"]=False       
    # Prepro section
    try:
        dictConfig["ungrib"]=TestOptionBoolean(config,'prepro','ungrib',logger)
    except:
        logger.warning( 'in section prepro ungrib is not defined or not well defined')
        logger.warning( 'ungrib must be a boolean: forced to true')
        dictConfig["ungrib"]=True
        
    
    try:
        dictConfig["dirIntermediateFile"]=config.get('prepro','dirIntermediateFile')
    except:
        logger.warning( 'in section prepro dirIntermediateFile is not defined')
        logger.warning( 'dirIntermediateFile forced to empty string')
        dictConfig["dirIntermediateFile"]=''
    else:
        try:
            dictConfig["prefixIntermediateFile"]=config.get('prepro','prefixIntermediateFile')
        except:
            logger.warning( 'in section prepro prefixIntermediateFile is not defined')
            logger.warning( 'dirIntermediateFile forced to empty string')
            logger.warning( 'ungrib forced to True')            
            dictConfig["dirIntermediateFile"]=''  
            dictConfig["ungrib"]=True     
        
        
    if dictConfig["ungrib"] and dictConfig["dirIntermediateFile"]!='':
        logger.warning( 'in section prepro dirIntermediateFile is defined and ungrib=True')
        logger.warning( 'ungrib forced to False to use dirIntermediateFile')
        dictConfig["ungrib"]=False

    
    try:
        dictConfig["geogrid"]=TestOptionBoolean(config,'prepro','geogrid',logger)
    except:
        logger.warning( 'in section prepro geogrid is not defined or not well defined')
        logger.warning( 'geogrid must be a boolean: forced to true')
        dictConfig["geogrid"]=True
        
    try:
        dictConfig["ECsigma"]=TestOptionBoolean(config,'prepro','ECsigma',logger)
        try:
            dictConfig["sigmaFile"]=config.get('prepro','sigmaFile')
        except:
            logger.warning( 'in section prepro sigmaFile is not defined')
            logger.warning( 'sigmaFile forced to empty string')
            logger.warning( 'ECsigma forced to False')
            dictConfig["sigmaFile"]=''
            dictConfig["ECsigma"]=False

    except:
        logger.warning( 'in section prepro ECsigma is not defined or not well defined')
        logger.warning( 'ECsigma must be a boolean: forced to False')
        dictConfig["ECsigma"]=False
        
    try:
        dictConfig["GeoTBLFile"]=config.get('prepro','GeoTBLFile')
    except:
        logger.warning( 'in section prepro GeoTBLFile is not defined')
        logger.warning( 'GeoTBLFile forced to empty string')
        dictConfig["GeoTBLFile"]=''
        
    try:
        dictConfig["MetTBLFile"]=config.get('prepro','MetTBLFile')
    except:
        logger.warning( 'in section prepro MetTBLFile is not defined')
        logger.warning( 'MetTBLFile forced to empty string')
        dictConfig["MetTBLFile"]=''
        
    dictConfig["prefixGriFile"]=config.get('prepro','prefixGribFile')
    try:
        dictConfig["dirGribFile"]=config.get('prepro','dirGribFile')
    except:
        logger.warning( 'in section prepro dirGribFile is not defined')
        logger.warning( 'dirGribFile forced to .')
        dictConfig["dirGribFile"]='./'
    try:
        dictConfig["vtableFile"]=config.get('prepro','vtableFile')
    except:
        logger.warning( 'in section prepro vtableFile is not defined')
        logger.warning( 'vtableFile must be present in WPS directory')
        logger.warning( 'and named Vtable')        
        dictConfig["vtableFile"]='./Vtable'    

    try:
        dictConfig["ungribSST"]=TestOptionBoolean(config,'prepro','ungribSST',logger)
    except:
        logger.warning( 'in section prepro ungribSST is not defined or not well defined')
        logger.warning( 'ungribSST must be a boolean: forced to False')
        dictConfig["ungribSST"]=False
    
    try:
        dictConfig["prefixSSTfile"]=config.get('prepro','prefixSSTfile')
    except:
        logger.warning( 'in section prepro prefixSSTfile is not defined')
        logger.warning( 'prefixSSTfile not used all actual gribfiles will be processed ')
        dictConfig["prefixSSTfile"]=''
        
       
    try:
        dictConfig["vtableSST"]=config.get('prepro','vtableSST')
    except:
        logger.warning( 'in section prepro vtableSST is not defined')
        logger.warning( 'vtableSST forced to ./Vtable.SST')
        dictConfig["vtableSST"]='./Vtable.SST'  

    try:
        dictConfig["TAVGSFC"]=TestOptionBoolean(config,'prepro','TAVGSFC',logger)
    except:
        logger.warning( 'in section prepro TAVGSFC is not defined')
        logger.warning( 'TAVGSFC forced to False')
        dictConfig["TAVGSFC"]=False 
        
    # Run section  
    try:
        dictConfig["real"]=TestOptionBoolean(config,'run','real',logger)
    except:
        logger.warning( 'in section run real is not defined or not well defined')
        logger.warning( 'real must be a boolean :  forced to True')        
        dictConfig["real"]=True
    else:
        if not dictConfig["real"]:
            try:
                dictConfig["dirRealFile"]=config.get('run','dirRealFile')
            except:
                logger.warning( 'in section run dirRealFile is not defined')
                logger.warning( 'real forced to True')
                dictConfig["real"]=True
        
    try:
        dictConfig["wrf"]=TestOptionBoolean(config,'run','wrf',logger)
    except:
        logger.warning( 'in section run wrf is not defined or not well defined')
        logger.warning( 'real must be a boolean :  forced to True')        
        dictConfig["wrf"]=True
       
    try:
        dictConfig["subjob"]=config.get('run','subjob',logger)
    except:
        logger.warning( 'in section run subjob is not defined')
        logger.warning( 'subjob must be ccub or criann: forced to ccub')
        dictConfig["subjob"]="ccub"
    else:
        if dictConfig["subjob"]!='ccub' and dictConfig["subjob"]!='criann':
            logger.warning( 'in section run subjob is not well defined')
            logger.warning( 'subjob must be ccub or criann): forced to qsub')
            dictConfig["subjob"]="ccub"            
        
    try:
        dictConfig["nbproc"]=config.getint('run','nbproc')
    except:
        logger.warning( 'in section run nbproc is not defined or not well defined')
        logger.warning( 'nbproc must be an integer :  forced to 16')        
        dictConfig["nbproc"]=16
 
    try:
        dictConfig["nbprocReal"]=config.getint('run','nbprocReal')
    except:
        logger.warning( 'in section run nbprocReal is not defined or not well defined')
        logger.warning( 'nbprocReal must be an integer :  forced to 8')        
        dictConfig["nbprocReal"]=8

    try:
        dictConfig["binding"]=TestOptionBoolean(config,'run','binding',logger)
    except:
        logger.warning( 'in section run binding is not defined or not well defined')
        logger.warning( 'binding must be a boolean: forced to false')
        dictConfig["binding"]=False



    try:
        dictConfig["dirMetFile"]=config.get('run','dirMetFile')
    except:
        logger.warning( 'in section run dirMetFile is not defined')
        logger.warning( 'dirMetFile forced to .')
        dictConfig["dirMetFile"]='./'
    try:
        dictConfig["dirGenMetFile"]=config.get('run','dirGenMetFile')
    except:
        logger.warning( 'in section run dirGenMetFile is not defined')
        logger.warning( 'dirGenMetFile forced to empty string')
        dictConfig["dirGenMetFile"]=''
    try:
        dictConfig["dirWrfFileToLink"]=config.get('run','dirWrfFileToLink')
    except:
        logger.warning( 'in section run dirWrfFileToLink is not defined')
        logger.warning( 'dirWrfFileToLink forced to empty string')
        dictConfig["dirWrfFileToLink"]=''        
    try:
        dictConfig["nodededic"]=config.get('run','nodededic')
    except:
        logger.warning( 'in section run nodededic is not defined')
        logger.warning( 'nodededic forced to empty string')
        dictConfig["nodededic"]=''
    
    if dictConfig["subjob"]=='ccub':
        try:
            dictConfig["madchinebind"]=config.get('run','machine')
        except:
            if dictConfig["binding"]:
                logger.info( 'in section run machine is not defined: forced to hauer with binding')
                dictConfig["madchinebind"]='hauer'
            else:            
                logger.info( 'in section run machine is not defined: forced to empty with no binding')
                dictConfig["madchinebind"]=''
            
        else:
            if dictConfig["madchinebind"]!='orff' and dictConfig["madchinebind"]!='hauer' \
                and dictConfig["madchinebind"]!='bach' and dictConfig["madchinebind"]!='part' \
                and dictConfig["madchinebind"]!='davis' and dictConfig["madchinebind"]!='verdi' \
                and dictConfig["madchinebind"]!='uv'and dictConfig["madchinebind"]!='bartok' :
                if dictConfig["binding"]:
                    logger.info( 'in section run machine is not defined: forced to orff with binding')
                    dictConfig["madchinebind"]='orff'
                else:            
                    logger.info( 'in section run machine is not defined: forced to empty with no binding')
                    dictConfig["madchinebind"]=''
    elif dictConfig["subjob"]=='criann':
        try:
            dictConfig["madchinebind"]=config.get('run','queue')
        except:     
            logger.info( 'in section run queue is not defined: forced to court')
            dictConfig["madchinebind"]='court'
            
        else:
            if dictConfig["madchinebind"]!='court' and dictConfig["madchinebind"]!='2tcourt' \
                and dictConfig["madchinebind"]!='tcourt' and dictConfig["madchinebind"]!='long' \
                and dictConfig["madchinebind"]!='tlong' and dictConfig["madchinebind"]!='tcourt_intra':
                logger.warning( 'in section run queue is not well defined: forced to court')
                dictConfig["madchinebind"]='court'        


    return dictConfig


#
##@param config : a configparser object
##@param section : section containing the option
##@param option : option that will be tested as boolean
##@brief Test if an option is boolean, if not put it to False 
##@return flagLogical : the value of the option modified or not         
def TestOptionBoolean(config,section,option,logger):
           
    try:    
        flagLogical = config.getboolean(section,option)
    except ValueError:
        logger.warning( section+' '+option+' is not boolean ')
        flagLogical=True
    return flagLogical


def TestOptionDate(config,section,option,logger):
        
    dateStr = config.get(section,option)
    try:
        res = re.match(".*(\d\d\d\d)-(\d\d)-(\d\d).+(\d\d):(\d\d):(\d\d).*",dateStr)
        if res:
            year = int(res.group(1))
            month = int(res.group(2))
            day = int(res.group(3))
            hour = int(res.group(4))
            minute = int(res.group(5))
            second = int(res.group(6))
            timeDate = dtime.datetime(year,month,day,hour,minute,second)
        else :
            raise ValueError('Invalid format')
    except ValueError:
        logger.error( section+' '+option+' has not got the good format')
        logger.error( 'YYYY-MM-DD hh:mm:ss')
        sys.exit()
        
    return timeDate
 

