# -*- coding: utf-8 -*-
"""
@File:          ImportMaps.py
@Description:   
@Author:        Tony Che
@Create Date:   2020-07-31
@Revision History:
"""

import os
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\ImportMaps9898.conf'


def ImportMaps(application=None, configFile=''):
    """ ImportMaps
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
            mapFolder = config.get('ImportMapFolder', None)
            if mapFolder is None:
                PrintMessage('Please define the map folder firstly.', 'Error')
                return False
            mapFiles = os.listdir(mapFolder)
            for mapFile in mapFiles:
                if mapFile.endswith('map'):
                    filename = os.path.join(mapFolder, mapFile)
                    print('Import map: ', filename)
                    info = app.ImportMap(filename)
            PrintMessage(CurrentMethodName(), ' complete.')
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret


if __name__ == "__main__":
    ImportMaps()

