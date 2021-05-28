# Create by Tony Che at 2020-01

# DevicesCountInDomain.py
# Feature description

import json
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\DevicesCountInDomain31200.conf'

def DevicesCountInDomain(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        app = NetBrainDB(config)
        if app.Login():
            dbDomain = app.GetDatabase(config['Domain Name'])
            subTypeNames = dbDomain.Device.distinct('subTypeName')
            for subTypeName in subTypeNames:
                deviceCountById = dbDomain.Device.count_documents({'subTypeName': subTypeName})
                print(''.join([str(subTypeName), ": ", str(deviceCountById)]))
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        app.Logout()
        return ret


if __name__ == "__main__":
    DevicesCountInDomain()

