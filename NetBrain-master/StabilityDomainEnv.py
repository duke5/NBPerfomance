# Create by Tony Che at 2020-01

# StabilityDomainEnv.py
# Feature description

import json
import Domain
import os
import ActivateOnline
import DeviceGroup
import ScheduleTask
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\StabilityDomainEnv31200.conf'

def StabilityDomainEnv(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True

        app = None
        #ret = ActivateOnline.ActivateOnline(config)
        if ret:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
        else:
            PrintMessage('StabilityDomainEnv failed.', 'Error')
            return False
        if app is None:
            return False
        if app.Login():
            app.ApplyTenantAndDomain(config['DomainInfo']['Tenant Name'], config['DomainInfo']['Domain Name'])
            # 1：Create Stability Domain
            ret = Domain.CreateDomain(app, config)
            if not ret:
                return False
            DiscoveryAllTestEnv(app, config)
            #return True
            LoadingSiteDefine(app, config)

            ImportTestMap(app, config)
            EnableChangeAnalysis(app, config)
            InitScheduleTask(app, config)
            CreateBenchmarks(app, config)
            # Create10KDeviceGroup(app, config)
            StartScheduleTasks(app, config)
            # Create10KDeviceGroup(app, config)
    except Exception as e:
        PrintMessage('StabilityDomainEnv Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if app is not None and app.Logined:
            app.Logout()
        return ret

def DiscoveryAllTestEnv(app, config):
    DiscoveryBigDataEnv(app, config)
    Discovery1KEnv(app, config)
    #DiscoveryUSMIMIC8Env(app, config)
    DiscoveryBJRackEnv(app, config)
    DiscoveryUSMVSEmulatorEnv(app, config)
    #DiscoveryUSDemoIPEnv(app, config)
    DiscoverySDNEnv(app, config)
    return True

def DiscoveryBigDataEnv(app, config):
    '''
    2：Discvoery Big Data Env (modify FS config before)
    3：Import Network Define Table ---file：\\192.168.33.101\\temp\\User\\chengpu\\StabilityTestData\\NetworkDefine
    4: Add Network Settings(Telnet/Privilege: netbrain/netbrain)
    5: Import Big Data IP list to discovery  ---file：\\192.168.33.101\\temp\\User\\chengpu\\StabilityTestData\\IPList
    6: Create A Device Group for big data
    '''
    config['DiscoverInfo'] = config['DiscoverInfoBigData']
    config['GroupInfo'] = config['GroupInfoBigData']
    for info in config['DiscoverInfo']['NetworkDefineTableFilePath']:
        app.ImportNetworkDefineTable(info)
    for info in config['DiscoverInfo']['TelnetInfo']:
        app.UpdateTelnetInfo(info)
    for info in config['DiscoverInfo']['EnablePasswdInfo']:
        app.UpdateEnablePasswd(info)
    print(CurrentMethodName())
    Domain.StartDiscover(app, config)
    for info in config['DiscoverInfo']['TelnetInfo']:
        app.DeleteTelnetInfo(info.get('Alias', ''))
    for info in config['DiscoverInfo']['EnablePasswdInfo']:
        app.DeleteEnablePasswd(info.get('Alias', ''))
    return True

def DiscoveryUSMIMIC8Env(app, config):
    '''
    6:   Discovery US MIMIC8
    7:   Add Network Settings (Telnet/Privilege/SNMP: nb/nb/nb)
    8:   Discovery MIMIC8 IP list -- 31.38.0.1-31.38.19.135
         Create a Device Group for MIMIC8
    '''
    config['DiscoverInfo'] = config['DiscoverInfoUSMIMIC8']
    config['GroupInfo'] = config['GroupInfoUSMIMIC8']
    for info in config['DiscoverInfo']['TelnetInfo']:
        app.UpdateTelnetInfo(info)
    for info in config['DiscoverInfo']['EnablePasswdInfo']:
        app.UpdateEnablePasswd(info)
    for info in config['DiscoverInfo']['SnmpRoInfo']:
        app.UpdateSnmpRoInfo(info)
    print(CurrentMethodName())
    Domain.StartDiscover(app, config)
    for info in config['DiscoverInfo']['TelnetInfo']:
        app.DeleteTelnetInfo(info.get('Alias', ''))
    for info in config['DiscoverInfo']['EnablePasswdInfo']:
        app.DeleteEnablePasswd(info.get('Alias', ''))
    for info in config['DiscoverInfo']['SnmpRoInfo']:
        app.DeleteSnmpRoInfo(info.get('Alias', ''))
    return True

def DiscoveryBJRackEnv(app, config):
    '''
    9:  Discovery BJ-Rack
    10: Import Network Settings  --file: \\192.168.33.101\\temp\\User\\chengpu\\StabilityTestData\\Network Settings
    11: Discovery 10.10.7.253 Depths 30
    12: Create a Device Group for BJ-Rack
    '''
    config['DiscoverInfo'] = config['DiscoverInfoBJRack']
    config['GroupInfo'] = config['GroupInfoBJRack']
    print(CurrentMethodName())
    Domain.StartDiscover(app, config)
    return True

def DiscoveryUSMVSEmulatorEnv(app, config):
    '''
    13: Discovery US MVS emulator
    14: Import Network Settings ---file: \\192.168.33.101\\temp\\User\\chengpu\\StabilityTestData\\Network Settings
    15: Discovery IP list  \\192.168.33.101\\temp\\User\\chengpu\\StabilityTestData\\IPList
    16: Create a Device Group for MVS
    '''
    config['DiscoverInfo'] = config['DiscoverInfoUSMVSEmulator']
    config['GroupInfo'] = config['GroupInfoUSMVSEmulator']
    print(CurrentMethodName())
    Domain.StartDiscover(app, config)
    return True

def DiscoveryUSDemoIPEnv(app, config):
    '''
    17: Discovery US Demo IP
    18: Import Network Settings --File: \\192.168.33.101\\temp\\User\\chengpu\\StabilityTestData\\Network Settings
    19: Discovery IP list --file: \\192.168.33.101\\temp\\User\\chengpu\\StabilityTestData\\IPList
    20: Create a Device Group for Demo
    '''
    config['DiscoverInfo'] = config['DiscoverInfoUSDemoIP']
    config['GroupInfo'] = config['GroupInfoUSDemoIP']
    print(CurrentMethodName())
    Domain.StartDiscover(app, config)
    return True

def DiscoverySDNEnv(app, config):
    '''
    21: Discovery SDN
    22: Import API Server Manager -- file: \\192.168.33.101\\temp\\User\\chengpu\\StabilityTestData\\SDNAPImanager
    23: Import Network Settings -- file \\192.168.33.101\temp\\User\\chengpu\\StabilityTestData\\Network Settings
    24: Discovery SDN IP --file : \\192.168.33.101\\temp\\User\\chengpu\\StabilityTestData\\IPList
    25: Create A Device Group for SDN
    '''
    config['DiscoverInfo'] = config['DiscoverInfoSDN']
    config['GroupInfo'] = config['GroupInfoSDN']
    print(CurrentMethodName())
    Domain.StartDiscover(app, config)
    return True

def Discovery1KEnv(app, config):
    config['DiscoverInfo'] = config['DiscoverInfo1K']
    config['GroupInfo'] = config['GroupInfo1K']
    for info in config['DiscoverInfo']['TelnetInfo']:
        app.UpdateTelnetInfo(info)
    for info in config['DiscoverInfo']['EnablePasswdInfo']:
        app.UpdateEnablePasswd(info)
    for info in config['DiscoverInfo']['SnmpRoInfo']:
        app.UpdateSnmpRoInfo(info)
    print(CurrentMethodName())
    Domain.StartDiscover(app, config)
    return True

def ImportTestMap(app, config):
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
    return True

def LoadingSiteDefine(app, config):
    print(CurrentMethodName())
    app.LoadSiteDefinition(config['LoadingSiteDefineFilename'])
    return True

def EnableChangeAnalysis(app, config):
    app.EnableChangeAnalysis(config['Change Analysis Setting'])
    return True

def InitScheduleTask(app, config):
    config['Tenant Name'] = config['DomainInfo']['Tenant Name']
    config['Domain Name'] = config['DomainInfo']['Domain Name']
    ScheduleTask.SaveScheduleDiscovery(app, config)
    ScheduleTask.SaveScheduleBenchmark(app, config)
    ScheduleTask.SaveScheduleDataViewTemplate(app, config)
    return True

def StartScheduleTasks(app, config):
    ScheduleTask.StartScheduleTasks(app, config)
    return True

def Create10KDeviceGroup(app, config):
    # Create 10k Device Group  more than 1device
    '''
    deviceGroupInfo = config['DeviceGroupInfo'].copy()
    for index in range(1, 4):
        name = ''.join([deviceGroupInfo['Name'], f'{index:05}'])
        config['DeviceGroupInfo']['Name'] = name
        print(''.join([str(index), ': ', name]))
    '''
    ret = DeviceGroup.AddDeviceGroup(app, config)
    return True

def Create10KSite():
    # Create 10k Device Group  more than 1device
    return True

def CreateBenchmarks(app, config):
    ScheduleTask.AddScheduleBenchmarks(app, config)
    return True


if __name__ == "__main__":
    StabilityDomainEnv()

