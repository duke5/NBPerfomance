# Create by Tony Che at 2020-01

# ScheduleTask.py
# Feature description

import json
import csv
import re
from datetime import datetime, timedelta
from time import sleep
from NetBrainDB import NetBrainDB
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\ScheduleTask30198.conf'
#ConfigFile = r'.\conf\ScheduleTask31200.conf'

def ScheduleTask():
    ret = False
    # ret = SaveScheduleDiscovery()
    # if ret:
    #     ret =SaveScheduleBenchmark()
    # if ret:
    #     ret = SaveScheduleDataViewTemplate()
    #for index in range(10):
        #print(f'loop {index}:')
    StartScheduleTasks()
    #ExportScheduleDataViewTemplateLog()
    # if ret:
    #     AddScheduleBenchmarks()
    return True

def SaveScheduleDiscovery(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('Save Schedule Discovery')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        else:
            app = application
        if app.Logined:
            ret = app.SaveScheduleDiscovery(config['ScheduleDiscoveryInfo'])
    except Exception as e:
        PrintMessage('SaveScheduleDiscovery Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def SaveScheduleBenchmark(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('Save Schedule Benchmark')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        else:
            app = application
        if app.Logined:
            benchmarkInfo = config.get('ScheduleBenchmarkInfo', None)
            if benchmarkInfo is None:
                benchmarkInfo = config['ScheduleBenchmarkInfoAll']
            ret = app.SaveScheduleBenchmark(benchmarkInfo)
    except Exception as e:
        PrintMessage('SaveScheduleBenchmark Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def SaveScheduleDataViewTemplate(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('Save Schedule DataViewTemplate')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        else:
            app = application
        if app.Logined:
            ret = app.SaveScheduleDataViewTemplate(config['ScheduleDataViewTemplateInfo'])
    except Exception as e:
        PrintMessage('SaveScheduleDataViewTemplate Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def AddScheduleBenchmarks(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False

    try:
        ret = True
        print('Add Schedule Benchmarks')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        else:
            app = application
        if app.Logined:
            benchmarkCount = config.get('ScheduleBenchmarkInfoCount', 1) + 1
            if benchmarkCount <= 2:
                ret = app.SaveScheduleBenchmark(config['ScheduleBenchmarkInfo'])
            else:
                for index in range(1, benchmarkCount):
                    name = f'ScheduleBenchmarkInfo{index:02}'
                    benchmarkInfo = config.get(name, {})
                    if len(benchmarkInfo) <= 0:
                        continue
                    print(f'{index:02}: ' + benchmarkInfo['Task Name'])
                    ret = app.SaveScheduleBenchmark(benchmarkInfo)
                    if not ret:
                        PrintMessage(''.join([CurrentMethodName(), 'Failed to save the configuration: ', name]),
                                     'Warning')
        else:
            PrintMessage(''.join([CurrentMethodName(), ': please log into system.']), 'Error')
    except Exception as e:
        PrintMessage('AddScheduleBenchmarks Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def StartScheduleTasks(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('Start Schedule Tasks')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
        else:
            app = application
        if app.Logined:
            tenantName = config.get('Tenant Name', None)
            if tenantName is None:
                tenantName = config.get('DomainInfo', {}).get('Tenant Name', None)
            if tenantName is None:
                PrintMessage('Tenant Name is not existed.', 'Error')
                return False
            domainName = config.get('Domain Name', None)
            if domainName is None:
                domainName = config.get('DomainInfo', {}).get('Domain Name', None)
            if domainName is None:
                PrintMessage('Domain Name is not existed.', 'Error')
                return False
            app.ApplyTenantAndDomain(tenantName, domainName)
            for name in config.get('Schedule Discovery/Benchmark', []):
                print(''.join(['StartScheduleTasks: ', name]))
                app.StartBenchmarkTask(name)
                for x in range(10):
                    app._getAllBenchmarkDefinitions()
                    sleep(60)
            for name in config.get('Schedule Data View Template/Parser', []):
                print(''.join(['StartScheduleTasks: ', name]))
                app.StartScheduleDVT(name)
                for x in range(10):
                    app._schedulerSearch()
                    sleep(60)
    except Exception as e:
        PrintMessage('StartScheduleTasks Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def ExportScheduleDataViewTemplateLog(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('ExportScheduleDataViewTemplateLog')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
            tenantName, domainName = NetBrainUtils.GetTenantAndDomainName(config)
            if tenantName is None or domainName is None:
                PrintMessage(''.join(['Tenant Name (', tenantName, ') or Domain Name (',
                                      domainName, ') do NOT exist.']), 'Error')
                return False
            app.ApplyTenantAndDomain(tenantName, domainName)
        else:
            app = application
        if app.Logined:
            scheduleTask = config.get('Schedule Data View Template/Parser Task', None)
            if scheduleTask is None:
                PrintMessage('Please set Task in config file.', 'Error')
                return False
            taskName = scheduleTask.get('Task Name', '')
            taskStartTimes = scheduleTask.get('Start Time', [])
            outputFolder = scheduleTask.get('Output Folder', None)
            if outputFolder is None:
                PrintMessage('Please set the output folder.', 'Error')
                return False
            if outputFolder.endswith('//'):
                outputFolder += '//'
            for startTime in taskStartTimes:
                #print(taskName, startTime)
                strStartTime = NetBrainUtils.StringToDateTime(startTime, '%m/%d/%Y, %I:%M:%S %p')
                strStartTime = NetBrainUtils.DateTimeToString(strStartTime, 3)
                executionLogFilename = ''.join([outputFolder, taskName, '_ExecutionLog_', strStartTime, '.csv'])
                dvtFilename = ''.join([outputFolder, taskName, '_QualificationResult_DVT_', strStartTime, '.csv'])
                parserFilename = ''.join([outputFolder, taskName, '_QualificationResult_Parser_', strStartTime, '.csv'])
                info = app.GetScheduleDataViewTemplateTaskViewLogs(taskName, startTime)
                if len(info) <= 0:
                    PrintMessage(''.join([CurrentMethodName(), ': failed to find the log of task "',
                                          taskName, '" at ', startTime, '.']), 'Warning')
                    continue
                taskExecutionID = info['id']
                qualificationInfo = app.GetScheduleDataViewTemplateTaskQualification(taskExecutionID)
                info = app.GetScheduleDataViewTemplateTaskExecutionLog(taskExecutionID)
                if len(info):
                    for item in info:
                        item['name'] = ''
                        '''
                        if '.' in item['time']:
                            item['time'] = NetBrainUtils.StringToDateTime(item['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                        else:
                            item['time'] = NetBrainUtils.StringToDateTime(item['time'], '%Y-%m-%dT%H:%M:%SZ')
                        '''
                        if item['message'].startswith('No qualified devices'):
                            continue
                        if re.match('.*Data View Template[\w\W]*', item['message'], re.I):
                            for value in qualificationInfo['DVTQualifications']:
                                name = value['name']
                                if name in item['message']:
                                    item['name'] = f'DVT_{name}'
                                    item['path'] = value['path']
                                    break
                        elif re.match('.* parser[\w\W]*', item['message'], re.I):  #' parser' in item['message']:
                            name = re.match('.* for the (.*?) parser', item['message'], re.I)
                            path = '' if name is None else name.groups()[0]
                            for value in qualificationInfo['parserQualifications']:
                                name = value['name']
                                if name in item['message']:
                                    item['name'] = f'Parser_{name}'
                                    item['path'] = path
                                    break
                    with open(executionLogFilename, 'w', newline='') as csvFile:
                        writer = csv.DictWriter(csvFile, fieldnames=['time', 'message', 'name', 'path', 'id', 'level',
                                                                     'scheduleTaskId', 'scheduleTaskExecutionId'])
                        writer.writeheader()
                        writer.writerows(row for row in info)
                else:
                    PrintMessage(''.join([CurrentMethodName(), ': there is no Excution Log for the task "',
                                          taskName, '" at ', startTime, '.']), 'Warning')
                if len(qualificationInfo['DVTQualifications']):
                    with open(dvtFilename, 'w', newline='') as csvFile:
                        writer = csv.DictWriter(csvFile, fieldnames=['name', 'nodeCount', 'path', 'id'])
                        writer.writeheader()
                        writer.writerows(row for row in qualificationInfo['DVTQualifications'])
                else:
                    PrintMessage(''.join([CurrentMethodName(), ': No Qualification DVT info for the task "',
                                          taskName, '" at ', startTime, '.']), 'Warning')
                if len(qualificationInfo['parserQualifications']):
                    with open(parserFilename, 'w', newline='') as csvFile:
                        writer = csv.DictWriter(csvFile, fieldnames=['name', 'nodeCount', 'path', 'id'])
                        writer.writeheader()
                        writer.writerows(row for row in qualificationInfo['parserQualifications'])
                else:
                    PrintMessage(''.join([CurrentMethodName(), ': No Qualification Parser info for the task "',
                                          taskName, '" at ', startTime, '.']), 'Warning')
    except Exception as e:
        PrintMessage('ExportScheduleDataViewTemplateLog Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def ExportScheduleDataViewXFDTG(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        db = None
        print('ExportScheduleDataViewXFDTG')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
            tenantName, domainName = NetBrainUtils.GetTenantAndDomainName(config)
            if tenantName is None or domainName is None:
                PrintMessage(''.join(['Tenant Name (', tenantName, ') or Domain Name (',
                                      domainName, ') do NOT exist.']), 'Error')
                return False
            app.ApplyTenantAndDomain(tenantName, domainName)
        else:
            app = application
        if app.Logined:
            db = NetBrainDB(config['DB Info'])
            db.Login()
            if not db.Logined:
                PrintMessage(''.join([CurrentMethodName(), ': Failed to login MongoDB.']), 'Error')
                return False
            db.GetDatabase('flowengine')
            schedule_dvt_list = app._getSchedulerDataViewTemplate()
            scheduleTask = config.get('Schedule Data View Template/Parser Task', None)
            if scheduleTask is None:
                PrintMessage('Please set Task in config file.', 'Error')
                return False
            taskName = scheduleTask.get('Task Name', '')
            schedule_dvt = next((item for item in schedule_dvt_list if item.get('name', None) == taskName), None)
            if schedule_dvt is None:
                PrintMessage(f'Failed to find Schedule Task "{taskName}".', 'Error')
                return False
            job_id = schedule_dvt.get('jobId', None)
            if job_id is None:
                PrintMessage(f'Failed to find jobId in "{schedule_dvt}".', 'Error')
                return False
            taskStartTimes = scheduleTask.get('Start Time', [])
            outputFolder = scheduleTask.get('Output Folder', None)
            if outputFolder is None:
                PrintMessage('Please set the output folder.', 'Error')
                return False
            if outputFolder.endswith('//'):
                outputFolder += '//'
            for startTime in taskStartTimes:
                #print(taskName, startTime)
                start_time = NetBrainUtils.StringToDateTime(startTime, '%m/%d/%Y, %I:%M:%S %p')
                start_time_utc = NetBrainUtils.LocalTimeToUTCTime(start_time, -4)
                one_minute = timedelta(minutes=1)
                strStartTime = NetBrainUtils.DateTimeToString(start_time, 3)
                dtgFilename = ''.join([outputFolder, taskName, '_XFDTG_', strStartTime, '.csv'])
                filter = {'jobId': job_id,
                          'submitTime': {"$gt": start_time_utc - one_minute, "$lt": start_time_utc + one_minute}}
                xf_taskflow = db.GetOne('XFTaskflow', filter)
                if len(xf_taskflow) <= 0:
                    PrintMessage(''.join([CurrentMethodName(), ': failed to find the taskflow of task "',
                                          taskName, '" at ', startTime, '.']), 'Warning')
                    continue
                xf_dtg = db.GetAll('XFDtg', {'taskflowId': xf_taskflow['_id']}, 'triggeredTaskParameters', 1)
                if len(xf_dtg) <= 0:
                    PrintMessage(''.join([CurrentMethodName(), ': no dtg available.']), 'Warning')
                    continue
                xf_dtg_list = []
                for item in xf_dtg:
                    trigger_task = json.loads(item['triggeredTaskParameters'])
                    submit_time = item['submitTime']
                    trigger_time = item['triggerTime']
                    dtg = {
                        'Parser Path': trigger_task['parserPath'],
                        'Duration': trigger_time - submit_time,
                        'Submit Time': submit_time,
                        'Trigger Time': trigger_time,
                        'DTG Status': item['dtgStatus'],
                        'ID': item['_id'],
                        'Triggered Task': json.dumps(trigger_task)
                    }
                    xf_dtg_list.append(dtg)
                with open(dtgFilename, 'w', newline='') as csvFile:
                    writer = csv.DictWriter(csvFile, fieldnames=['Parser Path', 'Duration', 'Submit Time',
                                                                 'Trigger Time', 'DTG Status', 'ID', 'Triggered Task'])
                    writer.writeheader()
                    writer.writerows(row for row in xf_dtg_list)
    except Exception as e:
        PrintMessage('ExportScheduleDataViewXFDTG Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        if db is not None and db.Logined:
            db.Logout()
        return ret


if __name__ == "__main__":
    try:
        #ScheduleTask()
        ExportScheduleDataViewTemplateLog()
        ExportScheduleDataViewXFDTG()
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
