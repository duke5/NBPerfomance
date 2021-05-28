# Create by Tony Che at 2020-02

# DeviceGroup.py
# Feature description

import json
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\DeviceGroup3197.conf'


def AddDeviceGroup(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            logined = app.Login()
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        else:
            app = application
            logined = True
        if logined:
            deviceGroupCount = config.get('DeviceGroupCount', None)
            config['DeviceGroupInfo']['DeviceGroupCount'] = 1 if deviceGroupCount is None else deviceGroupCount
            ret = app.SaveDeviceGroup(config['DeviceGroupInfo'])
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and logined:
            app.Logout()
        return ret


if __name__ == "__main__":
    AddDeviceGroup()

