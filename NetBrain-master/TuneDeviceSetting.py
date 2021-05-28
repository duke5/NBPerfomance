# -*- coding: utf-8 -*-
"""
@File:          TuneDeviceSetting.py
@Description:   并发执行Device Tune
@Author:        Tony Che
@Create Date:   2020-09-01
@Revision History:
"""

import json
import queue
import threading
import time
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\TuneDeviceSetting31110.conf'
inputQueue = queue.Queue()
outputQueue = queue.Queue()


def TuneDeviceSetting(application=None, configFile=''):
    """ TuneDeviceSetting
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
            site_id = app._getSiteID(config['Site Name'])
            device_name = config['Device Name']
            device_id = ''
            devices = app.getSiteDevicesBySiteIDWithFilter(site_id, device_name)
            if len(devices) < 0 or devices['totalCount'] <= 0:
                PrintMessage(''.join([CurrentMethodName(), 'Failed to find the device: ', device_name]), 'Error')
                return False
            for device in devices['memberList']:
                if device['deviceName'] == device_name:
                    device_id = device['deviceId']
                    break
            if device_id == '':
                PrintMessage(''.join([CurrentMethodName(), 'Failed to get the ID for device: ', device_name]), 'Error')
                return False
            device_setting = app.getSafeDeviceSettingByGuid(device_id)
            task_id = app.tuneDeviceSetting(device_setting).get('jobHandle', None)
            print(task_id)
            dbserver = NetBrainDB(config['DB Info'])
            flowEngine = dbserver.GetDatabase('flowengine')
            xfTask = flowEngine['XFTask']
            task_status = 0
            while task_status < 4:
                time.sleep(1)
                item = xfTask.find_one({'taskflowId': task_id})
                task_status = item.get('taskStatus', -1)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret


def TuneDeviceSettingMultiThread(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        tenantName = config['Tenant Name']
        domainName = config['Domain Name']
        maxThread = config.get('Thread Count', 1) + 1
        apps = list()
        if maxThread <= 2:
            TuneDeviceSetting(application, config)
            return ret
        for i in range(1, maxThread):
            username = ''.join([config['MultiThreadUsername'], f'{i:02}'])
            app = NetBrainIE(config['Url'], username, config['MultiThreadPassword'])
            if not app.Login():
                PrintMessage('Failed to login with the name: ' + username, 'Error')
                app = None
                continue
            apps.append(app)
            app.ApplyTenantAndDomain(tenantName, domainName)
            site_id = app._getSiteID(config['Site Name'])
            device_name = config['Device Name']
            device_id = ''
            devices = app.getSiteDevicesBySiteIDWithFilter(site_id, device_name)
            if len(devices) < 0 or devices['totalCount'] <= 0:
                PrintMessage(''.join([CurrentMethodName(), 'Failed to find the device: ', device_name]), 'Error')
                continue
            for device in devices['memberList']:
                if device['deviceName'] == device_name:
                    device_id = device['deviceId']
                    break
            if device_id == '':
                PrintMessage(''.join([CurrentMethodName(), 'Failed to get the ID for device: ', device_name]), 'Error')
                continue
            device_setting = app.getSafeDeviceSettingByGuid(device_id)
            inputQueue.put(device_setting)

        for i in range(1, maxThread):
            t = threading.Thread(target=StartWorkerThread, args=(apps[i-1], ))
            t.daemon = True
            t.start()

        # o = threading.Thread(target=OutputThread)
        # o.daemon = True
        # o.start()

        inputQueue.join()  # Block until all tasks are done
        # outputQueue.join()
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        for app in apps:
            if app.Logined:
                app.Logout()
    return ret


def WorkerThread(app, device_setting):
    try:
        ret = True
        if len(device_setting):
            PrintMessage(''.join(['-----------------------Tenant: ', app.TenantName, '; Domain: ', app.DomainName,
                                  '; User: ', app.Username, '. Tune start.---------------------\n']))
            taskID = app.tuneDeviceSetting(device_setting)
            # dbserver = NetBrainDB(config)
            PrintMessage(''.join(['-----------------------; User: ', app.Username, '. Tune Task ID: ',
                                  taskID['jobHandle'],'.---------------------\n']))
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        return ret


def StartWorkerThread(app):
    while True:
        device_setting = inputQueue.get()
        WorkerThread(app, device_setting)
        inputQueue.task_done()

    return True

if __name__ == "__main__":
    #TuneDeviceSetting()
    TuneDeviceSettingMultiThread()

