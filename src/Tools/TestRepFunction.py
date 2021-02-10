# -*- coding: utf-8 -*-

import os as os
import logging as logging
import shutil as shutil

def creatRep(source,rep,logger='',force=False):
    listDir=os.listdir(source)
    if rep in listDir:
        if force==False:
            if type(logger)!=logging.Logger:
                print(rep+' already exists in '+source)
            else:
                logger.info(rep+' already exists in'+source)
            return source+'/'+rep
        else:
            logger.info(rep+' already exists in'+source)
            logger.info(rep+' is going to be deleted in '+source)
            shutil.rmtree(source+'/'+rep,True)
    try:
        os.mkdir(source+'/'+rep)
        return source+'/'+rep
    except:
        if type(logger)!=logging.Logger:
            print('rep creation impossible')
        else:
            logger.error('rep creation impossible') 
            raise ValueError

        
 
