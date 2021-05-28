# Create by Tony Che at 2020-02

# SiteManager.py
# Feature description

import json
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\SiteManager31200.conf'


def SiteManager(application=None, configFile=''):
    AddSite(application, configFile)
    return True


def AllMultiSite(app, siteInfo, name, count, indexStart=1):
    #return
    index = 1
    if count == 1:
        print(''.join([siteInfo['Parent Path'], '\\', name]))
        ret = app.AddSite(siteInfo)
    else:
        start = 0
        end = count
        deviceIDs = siteInfo['DeviceIPs']
        while index <= count:
            siteInfo['Name'] = f'{name}{indexStart:05}'
            siteInfo['DeviceIPs'] = deviceIDs[start:end]
            print(''.join([siteInfo['Parent Path'], '\\', siteInfo['Name']]))
            ret = app.AddSite(siteInfo)
            indexStart += index
            start += count
            end += count
            index += 1
        siteInfo['DeviceIPs'] = deviceIDs[start:]
    if siteInfo['Category'] == 1:
        app._commitSite()
    return True

def AddSite(application=None, configFile=''):
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
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        else:
            app = application
        if app.Logined:
            app._unlockSite()
            ret = app._lockSite()
            if not ret:
                return ret
            if not app._environmentInit():
                #print('retry once')
                app._environmentInit()
            for siteInfo in config['Site Info']:
                siteInfo['Category'] = 1 if siteInfo['Category'].lower() == 'container' else 2
                deviceIPs = siteInfo['DeviceIPs']
                deviceIDs = app.DeviceIPtoID(deviceIPs)
                siteInfo['DeviceIPs'] = [x['ID'] for x in deviceIDs]
                name = siteInfo['Name']
                count = siteInfo['Site Count']
                parentCount = siteInfo.get('Parent Count', 1)
                parentPath = siteInfo['Parent Path']
                if parentPath.endswith('\\'):
                    parentPath = parentPath[:-1]
                    siteInfo['Parent Path'] = parentPath
                siteIndex = 1
                parentIndex = 1
                if parentCount <= 1:
                    AllMultiSite(app, siteInfo, name, count)
                else:
                    while parentIndex <= parentCount:
                        siteInfo['Parent Path'] = f'{parentPath}{parentIndex:05}'
                        AllMultiSite(app, siteInfo, name, count)
                        siteIndex += count
                        #del siteInfo['DeviceIPs'][0:count]
                        parentIndex += 1
            app._commitSite()
            ret = app._unlockSite()
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret


if __name__ == "__main__":
    SiteManager()

