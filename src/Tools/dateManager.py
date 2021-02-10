# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

import datetime as dtime
import re as re
import sys as sys
import dtrange as dtr

def dateRealManager(dateStartBloc,dateEndBloc,nml,logger,nbBloc,dictConfig):
    
    nbDomain=nml['domains']['max_dom']

    dateBegin=dateStartBloc
    dateEnd=dateEndBloc
    deltaDate=dateEnd-dateBegin
    if dictConfig['calendar']=='gregorian':
        nml['time_control']['run_days']=deltaDate.days
    else:
        nml['time_control']['run_days']=dictConfig["DayByBloc"]
    nml['time_control']['run_hours']=deltaDate.seconds//3600
    nml['time_control']['run_seconds']=deltaDate.seconds%3600
    nml['time_control']['run_minutes']=0
      
    yearSList=[]
    monthSList=[]
    daySList=[]
    hourSList=[]
    minuteSList=[]
    secondSList=[]
    yearEList=[]
    monthEList=[]
    dayEList=[]
    hourEList=[]
    minuteEList=[]
    secondEList=[]
    
    for i in range(0,nbDomain):
        yearSList.append(dateBegin.year)
        monthSList.append(dateBegin.month)
        daySList.append(dateBegin.day)
        hourSList.append(dateBegin.hour)
        minuteSList.append(dateBegin.minute)
        secondSList.append(dateBegin.second)
        yearEList.append(dateEnd.year)
        monthEList.append(dateEnd.month)
        dayEList.append(dateEnd.day)
        hourEList.append(dateEnd.hour)
        minuteEList.append(dateEnd.minute)
        secondEList.append(dateEnd.second)        
        
        
    nml['time_control']['start_year']=yearSList
    nml['time_control']['start_month']=monthSList
    nml['time_control']['start_day']=daySList
    nml['time_control']['start_hour']=hourSList
    nml['time_control']['start_minute']=minuteSList
    nml['time_control']['start_second']=secondSList

    nml['time_control']['end_year']=yearEList
    nml['time_control']['end_month']=monthEList
    nml['time_control']['end_day']=dayEList
    nml['time_control']['end_hour']=hourEList
    nml['time_control']['end_minute']=minuteEList
    nml['time_control']['end_second']=secondEList
    
    if nbBloc==0:
        nml['time_control']['restart']=False
    else:
        nml['time_control']['restart']=True
        
    logger.info('Process namelist before run')
    
    
    return nml

def dateRunManager(dictConfig,logger):
    dateList=[]

    try: 
        file=open('./dateList.txt','r')
    except:
        dateList=[]
        dateBegin=dictConfig['dateBegin']
        dateEnd=dictConfig['dateEnd']
        nbBloc= dictConfig["DayByBloc"]
        dateTmp=dateBegin
        deltaTime=dateEnd-dateBegin
        print(deltaTime)
        if deltaTime.days>nbBloc:
            while dateTmp<dateEnd:
                dateList.append(dateTmp)
                #dateTmp=dateTmp+dtime.timedelta(days=nbBloc)
                dateTmp=dtr.calendar.date_plus_days(dateTmp, nbBloc, calendar=dictConfig['calendar'])
        else:
            dateList.append(dateTmp)
        dateList.append(dateEnd)
        
    else:
        for row in file:
            dateTmp,boolTmp=TestOptionDate(row, logger)
            if boolTmp:
                dateList.append( dateTmp)
            else:
                logger.error('date '+row+ ' not in good format')
                sys.exit()
                
    return dateList

def TestOptionDate(dateStr,logger):
        
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
            TestDate=True
        else :
            raise ValueError('Invalid format')
    except ValueError:
        logger.warning( dateStr+' has not got the good format')
        logger.error( 'YYYY-MM-DD hh:mm:ss')
        TestDate=False

    return timeDate,TestDate