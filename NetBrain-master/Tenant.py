# Create by Tony Che at 2020-01

# Tenant.py
# Feature description

import json
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\Tenant31200.conf'

def AddTenant(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        app = NetBrainIE(config['Url'], config['Username'], config['Password'])
        if app.Login():
            ret = app.AddTenant(config['TenantInfo'])
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        app.Logout()
        return ret


if __name__ == "__main__":
    AddTenant()

