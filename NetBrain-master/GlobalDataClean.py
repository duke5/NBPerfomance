# -*- coding: utf-8 -*-
"""
@File:          GlobalDataClean.py
@Description:   
@Author:        Tony Che
@Create Date:   2021-02-21
@Revision History:
"""

import datetime
import traceback
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\GlobalDataClean31110.conf'


def GlobalDataClean(application=None, configFile=''):
    """ GlobalDataClean
    Parameter:
    ------------------------------------------
    application:
    configFile:
    
    Result:
    ------------------------------------------
    True
    
    Example:
    ------------------------------------------ 
    >> >
    >> >
    
    """
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False

    try:
        ret = True
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
        else:
            app = application
        if app.Logined:
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
            ret = app.GlobalDataClean(config[''])
    except Exception as e:
        PrintMessage(traceback.format_exc(), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def GetFrequencyType(type:str='BY DAY'):
    # frequency type: 0-RUN_ONCE, 1-By_SECOND, 2-BY_HOUR, 3-BY_DAY, 4-BY_WEEK, 5-BY_MONTH
    frequency_type = {
        'Run Once': 0,
        'By Second': 1
    }
    frequency_type =['RUN ONCE', 'BY SECOND', 'BY HOUR', 'BY DAY', 'BY WEEK', 'BY MONTH']
    type = type.upper()
    result = frequency_type.index(type) if type in frequency_type else 3
    return result

def GetTimeZoneOffset(time_zone:str):
    time_zone_offset = {
        'China Standard Time': 8,
        'Eastern Standard Time': -5
    }
    return time_zone_offset[time_zone]

def GetAutoCleanDataSchedule(db:NetBrainDB, local_time_zone:str='Eastern Standard Time'):
    # frequency type: 0-RUN_ONCE, 1-By_Second, 2-BY_HOUR, 3-BY_DAY, 4-BY_WEEK, 5-BY_MONTH
    frequency_type = {
        'Run Once': 0,
        'By Second': 1
    }
    db.GetDatabase('NGSystem')
    auto_clean = db.GetOne('JobDef', {'job.jobType' : 'AutoCleanData'})
    auto_clean_schedule = auto_clean['job']['scheduleTime']
    time_zone = auto_clean_schedule['timeZone']
    if auto_clean_schedule['frequency']['type'] == 3:
        seconds = auto_clean_schedule['frequency']['byDay']['timeRange'][0]['startTime']
        today = datetime.date.today()
        #start_time = datetime.datetime(today.year, today.month, today.day) + datetime.timedelta(seconds=seconds)
        start_time = datetime.timedelta(seconds=seconds)
        start_time_utc = NetBrainUtils.LocalTimeToUTCTime(start_time, GetTimeZoneOffset(time_zone))
        start_time_local = NetBrainUtils.UTCTimeToLocalTime(start_time_utc, GetTimeZoneOffset(local_time_zone))
        msg = ''.join(['Run Auto Clean at ', NetBrainUtils.DateTimeToString(start_time),
                       f' ({time_zone}), utc time ', NetBrainUtils.DateTimeToString(start_time_utc),
                       ', local time ', NetBrainUtils.DateTimeToString(start_time_local),
                       f' ({local_time_zone}) every day.'])
        auto_clean_schedule['start time'] = {'setting': start_time, 'utc': start_time_utc,
                                             'local': start_time_local, 'time zone': time_zone, 'message': msg}
    else:
        PrintMessage('Just support "By Day".', 'Error')
    return auto_clean_schedule

def SetAutoCleanDataSchedule(db:NetBrainDB, start_time:str='00:00:00', time_zone:str='Eastern Standard Time',
                             frequency_type:str='By Day'):
    if frequency_type != 'By Day':
        PrintMessage('Just support "By Day".', 'Error')
        return False
    db.GetDatabase('NGSystem')
    auto_clean = db.GetOne('JobDef', {'job.jobType' : 'AutoCleanData'})
    auto_clean_schedule = auto_clean['job']['scheduleTime']
    auto_clean_schedule['frequency']['type'] = GetFrequencyType(frequency_type)
    today = datetime.date.today()
    #dt = datetime.datetime.strptime(start_time.replace('/', '-'), '%Y-%m-%d %H:%M:%S')
    #dt -= datetime.datetime(today.year, today.month, today.day)
    dt = datetime.datetime.strptime(start_time, '%H:%M:%S') - datetime.datetime.strptime('0:0:0', '%H:%M:%S')
    value = {'timeRange': [{'startTime': dt.seconds, 'endTime': None}], 'interval': 1}
    auto_clean_schedule['frequency']['byDay'] = value
    auto_clean_schedule['timeZone'] = time_zone
    #save to db
    value = db.Update('JobDef', {'job.jobType' : 'AutoCleanData'}, auto_clean)
    return True if value['ok'] > 0 else False

def GetDataEngineCleanSchedule(db:NetBrainDB, local_time_zone:str='Eastern Standard Time'):
    db.GetDatabase('NGSystem')
    auto_clean = db.GetOne('JobDef', {'job.jobType' : 'DataEngineClean'})
    auto_clean_schedule = auto_clean['job']['scheduleTime']
    time_zone = auto_clean_schedule['timeZone']
    if auto_clean_schedule['frequency']['type'] == 3:
        seconds = auto_clean_schedule['frequency']['byDay']['timeRange'][0]['startTime']
        today = datetime.date.today()
        #start_time = datetime.datetime(today.year, today.month, today.day) + datetime.timedelta(seconds=seconds)
        start_time = datetime.datetime(today.year, today.month, today.day) + datetime.timedelta(seconds=seconds)
        start_time_utc = NetBrainUtils.LocalTimeToUTCTime(start_time, GetTimeZoneOffset(time_zone))
        start_time_local = NetBrainUtils.UTCTimeToLocalTime(start_time_utc, GetTimeZoneOffset(local_time_zone))
        msg = ''.join(['Run Data Engine Clean at ', NetBrainUtils.DateTimeToString(start_time),
                       f' ({time_zone}), utc time ', NetBrainUtils.DateTimeToString(start_time_utc),
                       ', local time ', NetBrainUtils.DateTimeToString(start_time_local),
                       f' ({local_time_zone}) every day.'])
        auto_clean_schedule['start time'] = {'setting': start_time, 'utc': start_time_utc, 'local': start_time_local,
                                             'time zone': time_zone, 'message': msg}
    elif auto_clean_schedule['frequency']['type'] == 4:
        seconds = auto_clean_schedule['frequency']['byWeek']['timeRange'][0]['startTime']
        day_of_week = NetBrainUtils.GetDayOfWeek(auto_clean_schedule['frequency']['byWeek']['day'][0])
        start_time = datetime.timedelta(seconds=seconds)
        start_time_utc = NetBrainUtils.LocalTimeToUTCTime(start_time, GetTimeZoneOffset(time_zone))
        start_time_local = NetBrainUtils.UTCTimeToLocalTime(start_time_utc, GetTimeZoneOffset(local_time_zone))
        msg = ''.join(['Run Data Engine Clean at ', NetBrainUtils.DateTimeToString(start_time),
                       f' ({time_zone}), utc time ', NetBrainUtils.DateTimeToString(start_time_utc),
                       ', local time ', NetBrainUtils.DateTimeToString(start_time_local),
                       f' ({local_time_zone}) on {day_of_week}.'])
        auto_clean_schedule['start time'] = {'setting': start_time, 'utc': start_time_utc, 'local': start_time_local,
                                             'time zone': time_zone, 'day': day_of_week, 'message': msg}
    else:
        PrintMessage('Just support "By Week" and "By Day".', 'Error')
    return auto_clean_schedule

def SetDataEngineCleanSchedule(db:NetBrainDB, start_time:str='2021-01-01 00:00:00', time_zone:str='Eastern Standard Time',
                             frequency_type:str='By Week'):
    if frequency_type not in ['By Day','By Week']:
        PrintMessage('Just support "By Week" and "By Day".', 'Error')
        return False
    db.GetDatabase('NGSystem')
    auto_clean = db.GetOne('JobDef', {'job.jobType' : 'DataEngineClean'})
    auto_clean_schedule = auto_clean['job']['scheduleTime']
    auto_clean_schedule['frequency']['type'] = GetFrequencyType(frequency_type)
    dt = datetime.datetime.strptime(start_time, '%H:%M:%S')
    dt -= datetime.datetime.strptime(start_time, '%H:%M:%S')
    value = {'timeRange': [{'startTime': dt.seconds, 'endTime': None}], 'interval': 1}
    auto_clean_schedule['frequency']['byDay'] = value
    auto_clean_schedule['timeZone'] = time_zone
    #save to db
    value = True  #db.Update('JobDef', {'job.jobType' : 'DataEngineClean'}, auto_clean)
    return True if value['ok'] > 0 else False

if __name__ == "__main__":
    config = NetBrainUtils.GetConfig(ConfigFile)
    if len(config) == 0:
        PrintMessage(''.join(['Failed to load the configuration file: ', ConfigFile]), 'Error')
        exit(1)

    try:
        ret = True
        app = NetBrainIE(config['Url'], config['Username'], config['Password'])
        app.Login()
        if app.Logined:
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
            #ret = GlobalDataClean(app, config)
        db = NetBrainDB(config['DB Info'])
        db.Login()
        db.GetDatabase(config['Domain Name'])
        run_schedule = GetAutoCleanDataSchedule(db)
        PrintMessage(run_schedule['start time']['message'])
        auto_clean = config['AutoCleanData']
        #SetAutoCleanDataSchedule(db, auto_clean['Start Time'], auto_clean['Time Zone'], auto_clean['Frequency Type'])
        run_schedule = GetDataEngineCleanSchedule(db)
        PrintMessage(run_schedule['start time']['message'])
        de_clean = config['DataEngineClean']
        #SetDataEngineCleanSchedule(db, de_clean['Start Time'], de_clean['Time Zone'], de_clean['Frequency Type'])
    except Exception as e:
        # traceback.print_exc()
        PrintMessage(traceback.format_exc(), 'Error')
        ret = False
    finally:
        if app.Logined:
            app.Logout()
        if db.Logined:
            db.Logout()

