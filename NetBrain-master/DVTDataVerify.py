# Create by Tony Che at 2020-01

# DVTDataVerify.py
# Feature description

import json
import random
from datetime import datetime
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\DVTDataVerify30198.conf'

def GetRandomItems(sources, maxCount=5):
    count = len(sources)
    if count <= maxCount:
        return sources
    indexs = [random.randint(0, count - 1) for x in range(maxCount)]
    #print('index: ', indexs)
    items = list()
    for index in indexs:
        items.append(sources[index])
    return items

def DVTDataVerify(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        app = NetBrainDB(config)
        if app.Login():
            dbName = config['Tenant Name'].replace(' ', '_')
            dbTenant = app.GetDatabase(dbName)
            dbName = config['Domain Name']
            dbDomain = app.GetDatabase(dbName)
            # FSC_DataTaskGroup
            fscDataTaskGroup = dbTenant['FSC_DataTaskGroup']
            #count = fscDataTaskGroup.estimated_document_count()  # count_documents({})
            #print(''.join(['FSC_DataTaskGroup has ', str(count), ' items.']))
            # ScheduleTaskExecution
            #count = dbDomain.ScheduleTask.estimated_document_count()  # count_documents({})
            name = config['Schedule DVT Name']
            scheduleTask = dbDomain.ScheduleTask.find_one({'name': name}, {'_id': 1, 'name': 1})
            #print(''.join(['ScheduleTask has ', str(count), ' items.\n']), scheduleTask)
            dvtStartTime = datetime.strptime(config['Schedule DVT Start Time'], '%m/%d/%Y, %I:%M:%S %p')
            dvtStartTime = app.LocalTimeToUTCTime(dvtStartTime)
            scheduleTaskExecution = dbDomain.ScheduleTaskExecution.find_one({'scheduleTaskId': scheduleTask['_id'],
                    '$and': [{'startExecuteTime': {'$gte': dvtStartTime}},
                             {'startExecuteTime': {'$lte': dvtStartTime.replace(microsecond=999999)}}]})
            startTime = scheduleTaskExecution['startExecuteTime'].replace(microsecond=0)
            endTime = scheduleTaskExecution['endExecuteTime']
            if endTime is None:
                endTime = datetime.strptime('0001-01-01 00:00:01', '%Y-%m-%d %H:%M:%S')
            dtgDetails = scheduleTaskExecution['DTGDetails']
            count = len(dtgDetails)
            print(''.join(['ScheduleTaskExecution ID: ', scheduleTaskExecution['_id'], ', DTG count: ', str(count),
                           ', startExecuteTime: ', startTime.strftime('%Y-%m-%d %H:%M:%S'),
                           ', endExecuteTime: ', endTime.strftime('%Y-%m-%d %H:%M;%S')]))
            info = GetRandomItems(dtgDetails)
            dtgIDs = list()
            for item in info:
                dtgIDs.append(item['DTGId'])
            index = 1
            deMetaData = list()
            for dtgID in dtgIDs:
                fscDTG = fscDataTaskGroup.find_one({'_id': dtgID})
                dtgActions = fscDTG['actions']
                print(''.join([f'{index} - DTG ID: ', dtgID, ', actions count: ', str(len(dtgActions))]))
                index += 1
                actions = GetRandomItems(dtgActions)
                dtgActions = list()
                for action in actions:
                    count = len(action['devices'])
                    print('\tdevices count: ', str(count))
                    deviceNames = GetRandomItems(action['devices'])
                    item = {'Parser': action['parser'],
                            'DeviceNames': deviceNames}
                    dtgActions.append(item)
                deMetaData.append(dtgActions)

            # Device
            device = dbDomain['Device']  # dbDomain.Device
            #count = device.estimated_document_count()  # count_documents({})
            #print(''.join(['Device has ', str(count), ' items.']))
            for action in deMetaData:
                for item in action:
                    conditions = {'$or': [{'name': x} for x in item['DeviceNames']]}
                    DeviceIDs = list(device.find(conditions))
                    item['DeviceIDs'] = [x['_id'] for x in DeviceIDs]

            # now = datetime.now()
            dayOfDVTStartTime = dvtStartTime.strftime('%d')
            name = ''.join(['DEMetaData_', str(dvtStartTime.year), '_', str(dvtStartTime.month)])
            DEMetaData = dbDomain[name]
            #count = DEMetaData.estimated_document_count()
            #print(''.join([name, ' has ', str(count), ' items.']))
            for action in deMetaData:
                for item in action:
                    conditions = {
                        'name': item['Parser'],
                        'day': int(dayOfDVTStartTime),
                        '$or': [{'devId': x} for x in item['DeviceIDs']]
                    }
                    print(''.join(['\nParser: ', item['Parser'], ', condition: ', str(conditions)]))
                    values = list(DEMetaData.find(conditions))
                    for value in values:
                        dataLists = value['dataList']
                        count = len(dataLists)
                        devID = value['devId']
                        index = item['DeviceIDs'].index(devID)
                        print(''.join(['device name: ', item['DeviceNames'][index], ', device id: ', devID,
                                       '; the length of dataList is ', str(count)]))
                        for dataList in dataLists:
                            runTime = dataList['time']
                            if runTime < dvtStartTime:
                                continue
                            print(dataList)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        app.Logout()
        return ret


if __name__ == "__main__":
    DVTDataVerify()

