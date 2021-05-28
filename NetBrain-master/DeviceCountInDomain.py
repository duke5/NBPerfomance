# -*- coding: utf-8 -*-
"""
@File:          DeviceCountInDomain.py
@Description:   
@Author:        Tony Che
@Create Date:   2020-05
@Revision History:
"""

import json
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\DeviceCountInDomain97124.conf'


def PrettyHumanSize(size, kb=1024, reserve=2):
    i = 0
    unit = {0 : 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > kb:
        size /= kb
        i += 1
    format = ''.join(['{:.', str(reserve), 'f}'])
    size = float(format.format(size))
    return ''.join([str(size), ' ', unit[i]])

def DeviceCountInDomain(application=None, configFile=''):
    """ DeviceCountInDomain
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
    > >>
    
    """
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False

    try:
        ret = True
        app = NetBrainDB(config)
        if app.Login():
            # call = app.command("dbstats")
            # database = call['db']
            # datasize = call['dataSize'] / 1024
            # objects = call['objects']
            # collections = call['collections']

            dbNames = app.GetDatabaseNames()
            for dbName in dbNames:
                collectionNames = app.GetCollectionNames(dbName)
                if 'Device' in collectionNames:
                    database = app.GetDatabase(dbName)
                    dbStats = app.GetStats(dbName)
                    dataSize = dbStats['dataSize']
                    device = database['Device']
                    count = device.count_documents({})
                    if count < 50:
                        PrintMessage(''.join(['The count of devices in domain "', dbName, '" is ', str(count),
                                  ', less then 50. ', 'Data Size is ', PrettyHumanSize(dataSize), '.']), 'Warning')
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret


if __name__ == "__main__":
    DeviceCountInDomain()

