# Create by Tony Che at 2020-01

# Domain.py
# Feature description

import json
import queue
import threading
import time
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\DomainCreate2400.conf'
inputQueue = queue.Queue()
outputQueue = queue.Queue()

def CreateDomain(application=None, configFile=''):
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
        else:
            app = application
            logined = True
        if logined:
            domainFrom = int(config.get('DomainFrom', 1))
            domainTo = int(config.get('DomainTo', 1)) + 1
            telnetInfo = config.get('TelnetInfo', {})
            enablePasswdInfo = config.get('EnablePasswdInfo', {})
            snmpRoInfo = config.get('SnmpRoInfo', {})
            telnetInfo2 = config.get('TelnetInfo2', None)
            enablePasswdInfo2 = config.get('EnablePasswdInfo2', None)
            snmpRoInfo2 = config.get('SnmpRoInfo2', None)
            if domainTo - domainFrom > 1:
                for i in range(domainFrom, domainTo):
                    domainInfo = config['DomainInfo'].copy()
                    domainName = domainInfo['Domain Name']
                    domainInfo['Domain Name'] = f'{domainName}{i:04}'
                    ret = app.CreateDomainWithNetworkSetting(domainInfo, telnetInfo, enablePasswdInfo, snmpRoInfo)
                    app.ApplyTenantAndDomain(domainInfo['Tenant Name'], domainInfo['Domain Name'])
                    if telnetInfo2 is not None:
                        app.UpdateTelnetInfo(telnetInfo2)
                    if enablePasswdInfo2 is not None:
                        app.UpdateEnablePasswd(enablePasswdInfo2)
                    if snmpRoInfo2 is not None:
                        app.UpdateSnmpRoInfo(snmpRoInfo2)
                    time.sleep(5)
            else:
                domainInfo = config['DomainInfo']
                ret = app.CreateDomainWithNetworkSetting(domainInfo, telnetInfo, enablePasswdInfo, snmpRoInfo)
                app.ApplyTenantAndDomain(config['DomainInfo']['Tenant Name'], config['DomainInfo']['Domain Name'])
            if telnetInfo2 is not None:
                app.UpdateTelnetInfo(telnetInfo2)
            if enablePasswdInfo2 is not None:
                app.UpdateEnablePasswd(enablePasswdInfo2)
            if snmpRoInfo2 is not None:
                app.UpdateSnmpRoInfo(snmpRoInfo2)
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        return False
    finally:
        if application is None and logined:
            app.Logout()
        return True


def StartDiscover(application=None, configFile=''):
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
        else:
            app = application
            logined = True
        if logined:
            app.ApplyTenantAndDomain(config['DomainInfo']['Tenant Name'], config['DomainInfo']['Domain Name'])
            for info in config['DiscoverInfo'].get('ImportAPIServerManagerInfo', []):
                app.ImportAPIServersV2(info)
            for info in config['DiscoverInfo'].get('ImportNetworkSettingInfo', []):
                app.ImportNetworkSetting(info)
            discoverTaskID = app.StartDiscover(config['DiscoverInfo'])
            app.SaveDeviceGroup(config['GroupInfo'], discoverTaskID)
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if application is None and logined:
            app.Logout()
        return ret


def StartDiscovers(application=None, configFile=''):
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
        else:
            app = application
            logined = True
        if logined:
            app.ApplyTenantAndDomain(config['DomainInfo']['Tenant Name'], config['DomainInfo']['Domain Name'])
            for info in config['DiscoverInfo'].get('ImportAPIServerManagerInfo', []):
                app.ImportAPIServersV2(info)
            for info in config['DiscoverInfo'].get('ImportNetworkSettingInfo', []):
                app.ImportNetworkSetting(info)
            count = config.get('DiscoverCount', 1) + 1
            if count > 2:
                for index in range(1, count):
                    discoverInfoName = ''.join(['DiscoverInfo', f'{index:02}'])
                    groupInfoName = ''.join(['GroupInfo', f'{index:02}'])
                    for info in config[discoverInfoName].get('ImportAPIServerManagerInfo', []):
                        app.ImportAPIServersV2(info)
                    for info in config[discoverInfoName].get('ImportNetworkSettingInfo', []):
                        app.ImportNetworkSetting(info)
                    discoverTaskID = app.StartDiscover(config[discoverInfoName])
                    app.SaveDeviceGroup(config[groupInfoName], discoverTaskID)
            else:
                StartDiscover(app, config)
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        if application is None and logined:
            app.Logout()
        return ret


def WorkerThread(app, tenantName, domainName, discoverInfo, groupInfo={}):
    try:
        ret = True
        app.ApplyTenantAndDomain(tenantName, domainName)
        if len(discoverInfo):
            PrintMessage(''.join(['-----------------------Tenant: ', tenantName, '; Domain: ', domainName,
                                  '; User: ', app.Username, '. Discover start.---------------------\n']))
            discoverTaskID = app.StartDiscover(discoverInfo)
            if len(groupInfo):
                app.SaveDeviceGroup(groupInfo, discoverTaskID)
            PrintMessage(''.join(['-----------------------Tenant: ', tenantName, '; Domain: ', domainName,
                                  '; User: ', app.Username, '. Discover complete.---------------------\n']))
            time.sleep(30)
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        return ret


def StartWorkerThread(app):
    while True:
        param = inputQueue.get()
        WorkerThread(app, param['TenantName'], param['DomainName'],
                     param['DiscoverInfo'], param['GroupInfo'])
        inputQueue.task_done()

    return True


def StartDiscoverMultiThread(configFile='', tenantName='', domainName='', discoverQueue=None):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        if tenantName == '':
            tenantName = config['DomainInfo']['Tenant Name']
        if domainName == '':
            domainName = config['DomainInfo']['Domain Name']
        maxThread = config.get('ThreadCount', 1) + 1
        domainFrom = int(config.get('DomainFrom', 1))
        domainTo = int(config.get('DomainTo', 1)) + 1
        apps = list()
        if maxThread <= 2:
            StartDiscover(None, config)
            return ret
        # Multi Thread
        if discoverQueue is None:
            for i in range(domainFrom, domainTo):
                theDomainName = ''.join([domainName, f'{i:04}'])
                discoverInfo = config.get('DiscoverInfoMulthThread', {})
                groupInfo = config.get('GroupInfoMulthThread', {})
                parameter = {'TenantName': tenantName, 'DomainName': theDomainName,
                         'DiscoverInfo': discoverInfo, 'GroupInfo': groupInfo}
                inputQueue.put(parameter)

        for i in range(1, maxThread):
            username = ''.join([config['MultiThreadUsername'], f'{i:02}'])
            app = NetBrainIE(config['Url'], username, config['MultiThreadPassword'])
            if not app.Login():
                PrintMessage('Failed to login with the name: ' + username, 'Error')
                app = None
                continue
            apps.append(app)
            t = threading.Thread(target=StartWorkerThread, args=(app,))
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


def StartMultiDomainDiscoverMultiThread(configFile='', tenantName='', domainName=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        if tenantName == '':
            tenantName = config['DomainInfo']['Tenant Name']
        if domainName == '':
            domainName = config['DomainInfo']['Domain Name']
        maxThread = config.get('DomainCount', 1) + 1
        threads = list()
        apps = list()
        if maxThread <= 2:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            if app.Login():
                apps.append(app)
                StartDiscover(app, config)
            else:
                StartDiscover(None, config)
        else:
            for i in range(1, maxThread):
                username = ''.join([config['MultiThreadUsername'], f'{i:02}'])
                app = NetBrainIE(config['Url'], username, config['MultiThreadPassword'])
                if not app.Login():
                    PrintMessage('Failed to login with the name: ' + username, 'Error')
                    continue
                theDomainName = ''.join([domainName, f'{i:02}'])
                discoverInfo = config.get(f'DiscoverInfo{i:02}', {})
                if len(discoverInfo):
                    continue
                groupInfo = config.get(f'GroupInfo{i:02}', {})
                t = threading.Thread(target=WorkerThread,
                                     args=(app, tenantName, theDomainName, discoverInfo, groupInfo))
                t.daemon = True
                threads.append(t)
                t.start()
                apps.append(app)
            for t in threads:
                t.join()  # Block until all tasks are done
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        for app in apps:
            app.Logout()
        return ret


def LoadIPsFromFile(filename):
    with open(filename, 'r') as txtFile:
        hostips = list(filter(None, txtFile.read().split(';')))
    return hostips

def ExportIPinFS(configFile, fsID, outFilename):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    app = NetBrainIE(config['Url'], config['Username'], config['Password'])
    domainInfo = config['DomainInfo']
    logined = app.Login()
    app.ApplyTenantAndDomain(domainInfo['Tenant Name'], domainInfo['Domain Name'])
    try:
        info = app._getFrontServerRefDevice(fsID)  # 'FS167'
        lines = ''
        ips = ''
        for item in info:
            lines += ''.join([item['mgmtIP'], ', ', item['name'], '\n'])
            ips += '\n'.join([item['mgmtIP']])
        with open(outFilename, 'w') as fp:  # r'c:\temp\fs167.txt'
            fp.write(lines)
            with open(outFilename+'.ip', 'w') as fp:  # r'c:\temp\fs167.txt'
                fp.write(ips)
    except Exception as e:
        print(str(e))
    app.Logout()


def DeleteDeviceGroups(configFile='', tenantName=None):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0 or tenantName is None:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        username = config['Username']
        app = NetBrainIE(config['Url'], username, config['Password'])
        if not app.Login():
            PrintMessage('Failed to login with the name: ' + username, 'Error')
            app = None
            return False
        tenantName = config[tenantName]['Tenant Name']
        domainName = config[tenantName]['Domain Name']
        domainFrom = config[tenantName]['DomainFrom']
        domainTo = config[tenantName]['DomainTo'] + 1
        for i in range(domainFrom, domainTo):
            theDomainName = f'{domainName}{i:04}'
            app.ApplyTenantAndDomain(tenantName, theDomainName)
            app.DeleteDeviceGroup(['FS168', 'FS68'], True)
            time.sleep(15)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return True

# Discover task start
def GenerateTenant1TaskQueue(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        tenantName = config['BTMSPTenant1']['Tenant Name']
        domainName = config['BTMSPTenant1']['Domain Name']
        #parameters = list()
        for i in range(8):
            discoverInfo = config['BTMSPTenant1']['DiscoverInfo'].copy()
            groupInfo = config['BTMSPTenant1']['GroupInfo'].copy()
            fsName = discoverInfo['_Front Server'][i]
            discoverInfo['Front Server'] = [fsName]
            discoverInfo['HostIPs'] = LoadIPsFromFile(discoverInfo['_HostIPs'][i])
            groupInfo['Name'] = fsName
            parameter = {'TenantName': tenantName, 'DomainName': domainName,
                     'DiscoverInfo': discoverInfo, 'GroupInfo': groupInfo}
            inputQueue.put(parameter)
            #parameters.append(parameter)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return ret


def GenerateTenant2TaskQueue(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        tenantName = config['BTMSPTenant2']['Tenant Name']
        domainName = config['BTMSPTenant2']['Domain Name']
        domainFrom = config['BTMSPTenant2']['DomainFrom']
        domainTo = config['BTMSPTenant2']['DomainTo'] + 1
        #parameters = list()
        ipFrom = 0
        index = 0
        hostIPs = None
        for i in range(domainFrom, domainTo):
            theDomainName = f'{domainName}{i:04}'
            discoverInfo = config['BTMSPTenant2']['DiscoverInfo'].copy()
            groupInfo = config['BTMSPTenant2']['GroupInfo'].copy()
            fsName = discoverInfo['_Front Server'][index]
            discoverInfo['Front Server'] = [fsName]
            groupInfo['Name'] = fsName
            if hostIPs is None:
                hostIPs = LoadIPsFromFile(discoverInfo['_HostIPs'][index])
            discoverInfo['HostIPs'] = hostIPs[ipFrom:ipFrom+50]
            parameter = {'TenantName': tenantName, 'DomainName': theDomainName,
                         'DiscoverInfo': discoverInfo, 'GroupInfo': groupInfo}
            inputQueue.put(parameter)
            #parameters.append(parameter)
            if ipFrom + 50 >= 10000:
                index += 1
                ipFrom = 0
                hostIPs = None
            else:
                ipFrom += 50
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return ret


def GenerateTenant3TaskQueue(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        parameters = list()
        for tenant in config['BTMSPTenant3']:
            tenantName = tenant['Tenant Name']
            domainName = tenant['Domain Name']
            domainFrom = tenant['DomainFrom']
            domainTo = tenant['DomainTo'] + 1
            domainNodes = tenant['DomainNodes']
            ipFrom = 0
            index = 0
            hostIPs = LoadIPsFromFile(tenant['DiscoverInfo']['_HostIPs'])
            for i in range(domainFrom, domainTo):
                theDomainName = f'{domainName}{i:04}'
                discoverInfo = tenant['DiscoverInfo'].copy()
                groupInfo = tenant['GroupInfo'].copy()
                fsName = discoverInfo['_Front Server'][index]
                discoverInfo['Front Server'] = [fsName]
                groupInfo['Name'] = fsName
                discoverInfo['HostIPs'] = hostIPs[ipFrom:ipFrom+domainNodes]
                parameter = {'TenantName': tenantName, 'DomainName': theDomainName,
                             'DiscoverInfo': discoverInfo, 'GroupInfo': groupInfo}
                inputQueue.put(parameter)
                #parameters.append(parameter)
                ipFrom += domainNodes
                index += 1
                if index > 3:
                    index = 0
            #index = len(parameters)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return ret


def GenerateTenant4TaskQueue(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        parameters = list()
        for tenant in config['BTMSPTenant4']:
            tenantName = tenant['Tenant Name']
            domainName = tenant['Domain Name']
            domainFrom = tenant['DomainFrom']
            domainTo = tenant['DomainTo'] + 1
            domainNodes = tenant['DomainNodes']
            ipFrom = 0
            index = 0
            hostIPs = None
            for i in range(domainFrom, domainTo):
                theDomainName = f'{domainName}{i:04}'
                discoverInfo = tenant['DiscoverInfo'].copy()
                groupInfo = tenant['GroupInfo'].copy()
                fscount = len(discoverInfo['_Front Server'])
                fsName = discoverInfo['_Front Server'][index]
                discoverInfo['Front Server'] = [fsName]
                groupInfo['Name'] = fsName
                hostIPNames = tenant['DiscoverInfo']['_HostIPs']
                if domainNodes >= 5000:
                    hostIPName = hostIPNames[index]
                else:
                    hostIPName = hostIPNames[0]
                if hostIPs is None:
                    hostIPs = LoadIPsFromFile(hostIPName)
                discoverInfo['HostIPs'] = hostIPs[ipFrom:ipFrom+domainNodes]
                parameter = {'TenantName': tenantName, 'DomainName': theDomainName,
                             'DiscoverInfo': discoverInfo, 'GroupInfo': groupInfo}
                inputQueue.put(parameter)
                parameters.append(parameter)
                ipFrom += domainNodes
                if fscount > 1:
                    index += 1
                    if index >= fscount:
                        index = 0
                if domainNodes >= 5000:
                    ipFrom = 0
                    hostIPs = None
            index = len(parameters)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return ret


def GenerateTenant5TaskQueue(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        parameters = list()
        for tenant in config['BTMSPTenant5']:
            tenantName = tenant['Tenant Name']
            domainName = tenant['Domain Name']
            domainFrom = tenant['DomainFrom']
            domainTo = tenant['DomainTo'] + 1
            domainNodes = tenant['DomainNodes']
            ipFrom = 0
            index = 0
            hostIPs = None
            for i in range(domainFrom, domainTo):
                theDomainName = f'{domainName}{i:04}'
                discoverInfo = tenant['DiscoverInfo'].copy()
                groupInfo = tenant['GroupInfo'].copy()
                fscount = len(discoverInfo['_Front Server'])
                fsName = discoverInfo['_Front Server'][index]
                discoverInfo['Front Server'] = [fsName]
                groupInfo['Name'] = fsName
                hostIPName = tenant['DiscoverInfo']['_HostIPs'][0]
                if hostIPs is None:
                    hostIPs = LoadIPsFromFile(hostIPName)
                discoverInfo['HostIPs'] = hostIPs[ipFrom:ipFrom+domainNodes]
                parameter = {'TenantName': tenantName, 'DomainName': theDomainName,
                             'DiscoverInfo': discoverInfo, 'GroupInfo': groupInfo}
                inputQueue.put(parameter)
                parameters.append(parameter)
                ipFrom += domainNodes
                if fscount > 1:
                    index += 1
                    if index >= fscount:
                        index = 0
            index = len(parameters)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return ret


def GenerateTenant6TaskQueue(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        parameters = list()
        for tenant in config['BTMSPTenant6']:
            tenantName = tenant['Tenant Name']
            domainName = tenant['Domain Name']
            domainFrom = tenant['DomainFrom']
            domainTo = tenant['DomainTo'] + 1
            domainNodes = tenant['DomainNodes']
            ipFrom = 0
            index = 0
            hostIPs = None
            for i in range(domainFrom, domainTo):
                theDomainName = f'{domainName}{i:04}'
                discoverInfo = tenant['DiscoverInfo'].copy()
                groupInfo = tenant['GroupInfo'].copy()
                fscount = len(discoverInfo['_Front Server'])
                fsName = discoverInfo['_Front Server'][index]
                discoverInfo['Front Server'] = [fsName]
                groupInfo['Name'] = fsName
                hostIPNames = tenant['DiscoverInfo']['_HostIPs']
                if domainNodes >= 5000:
                    hostIPName = hostIPNames[index]
                else:
                    hostIPName = hostIPNames[0]
                if hostIPs is None:
                    hostIPs = LoadIPsFromFile(hostIPName)
                discoverInfo['HostIPs'] = hostIPs[ipFrom:ipFrom+domainNodes]
                parameter = {'TenantName': tenantName, 'DomainName': theDomainName,
                             'DiscoverInfo': discoverInfo, 'GroupInfo': groupInfo}
                inputQueue.put(parameter)
                parameters.append(parameter)
                ipFrom += domainNodes
                if fscount > 1:
                    index += 1
                    if index >= fscount:
                        index = 0
                if domainNodes >= 5000:
                    ipFrom = 0
                    hostIPs = None
            index = len(parameters)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return ret


def DiscoverAmendment(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        #DeleteDeviceGroups(config, 'BTMSPTenant2')
        # for item in config['DiscoverAmendment']:
        #     for key, value in item.items():
        #         config[key] = value
        item = config.get('DiscoverAmendment', {}).get('BTMSPTenant1', None)
        if item is not None:
            config['BTMSPTenant1'] = item
            GenerateTenant1TaskQueue(config)
        item = config.get('DiscoverAmendment', {}).get('BTMSPTenant2', None)
        if item is not None:
            config['BTMSPTenant2'] = item
            GenerateTenant2TaskQueue(config)
        item = config.get('DiscoverAmendment', {}).get('BTMSPTenant3', None)
        if item is not None:
            config['BTMSPTenant3'] = item
            GenerateTenant3TaskQueue(config)
        item = config.get('DiscoverAmendment', {}).get('BTMSPTenant4', None)
        if item is not None:
            config['BTMSPTenant4'] = item
            GenerateTenant4TaskQueue(config)
        item = config.get('DiscoverAmendment', {}).get('BTMSPTenant5', None)
        if item is not None:
            config['BTMSPTenant5'] = item
            GenerateTenant5TaskQueue(config)
        item = config.get('DiscoverAmendment', {}).get('BTMSPTenant6', None)
        if item is not None:
            config['BTMSPTenant6'] = item
            GenerateTenant6TaskQueue(config)

        #taskQueue = list(inputQueue.queue)
        StartDiscoverMultiThread(configFile, '', '', inputQueue)
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        return ret
# Discover task end

def StartBTMSPDiscover(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    GenerateTenant2TaskQueue(config)
    GenerateTenant3TaskQueue(config)
    GenerateTenant4TaskQueue(config)
    GenerateTenant5TaskQueue(config)
    GenerateTenant6TaskQueue(config)
    GenerateTenant1TaskQueue(config)
    #taskQueue = list(inputQueue.queue)
    StartDiscoverMultiThread(configFile, '', '', inputQueue)
    return True


# Benchmark task start
def GenerateTenant1TaskQueueBenchmark(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        tenant = config['BTMSPTenant1']
        tenantName = tenant['Tenant Name']
        domainName = tenant['Domain Name']
        for benchmarkName in tenant['Schedule Discovery/Benchmark']:
            parameter = {'TenantName': tenantName, 'DomainName': domainName, 'BenchmarkName': benchmarkName}
            inputQueue.put(parameter)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return ret

def GenerateTenant2TaskQueueBenchmark(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        tenant = config['BTMSPTenant2']
        tenantName = tenant['Tenant Name']
        domainName = tenant['Domain Name']
        domainFrom = tenant['DomainFrom']
        domainTo = tenant['DomainTo'] + 1
        #parameters = list()
        for i in range(domainFrom, domainTo):
            theDomainName = f'{domainName}{i:04}'
            for benchmarkName in tenant['Schedule Discovery/Benchmark']:
                parameter = {'TenantName': tenantName, 'DomainName': theDomainName, 'BenchmarkName': benchmarkName}
                inputQueue.put(parameter)
            #parameters.append(parameter)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return ret

def GenerateTenant3to6TaskQueueBenchmark(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        tenantNames = ['BTMSPTenant3', 'BTMSPTenant4', 'BTMSPTenant5', 'BTMSPTenant6']
        for name in tenantNames:
            for tenant in config[name]:
                tenantName = tenant['Tenant Name']
                domainName = tenant['Domain Name']
                domainFrom = tenant['DomainFrom']
                domainTo = tenant['DomainTo'] + 1
                for i in range(domainFrom, domainTo):
                    theDomainName = f'{domainName}{i:04}'
                    for benchmarkName in tenant['Schedule Discovery/Benchmark']:
                        parameter = {'TenantName': tenantName, 'DomainName': theDomainName,
                                     'BenchmarkName': benchmarkName}
                        inputQueue.put(parameter)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        return ret


def StartWorkerThreadBenchmark(app):
    while True:
        if app is None:
            time.sleep(10)
            continue
        param = inputQueue.get()
        tenantName = param['TenantName']
        domainName = param['DomainName']
        benchmarkName = param['BenchmarkName']
        app.ApplyTenantAndDomain(tenantName, domainName)
        if len(benchmarkName):
            app.EnableBenchmark(benchmarkName)
            PrintMessage(''.join(['-----------------------Tenant: ', tenantName, '; Domain: ', domainName,
                                  '; User: ', app.Username, '. Benchmark start.---------------------\n']))
            app.StartBenchmarkTask(benchmarkName)
            PrintMessage(''.join(['-----------------------Tenant: ', tenantName, '; Domain: ', domainName,
                                  '; User: ', app.Username, '. Benchmark complete.---------------------\n']))
        time.sleep(30)
        inputQueue.task_done()

    return True


def StartBenchmarkMultiThread(configFile='', tenantName='', domainName='', benchmarkQueue=None):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        if tenantName == '':
            tenantName = config['DomainInfo']['Tenant Name']
        if domainName == '':
            domainName = config['DomainInfo']['Domain Name']
        maxThread = config.get('ThreadCount', 1) + 1
        domainFrom = int(config.get('DomainFrom', 1))
        domainTo = int(config.get('DomainTo', 1)) + 1
        apps = list()
        # Multi Thread
        if benchmarkQueue is None:
            for i in range(domainFrom, domainTo):
                theDomainName = ''.join([domainName, f'{i:04}'])
                parameter = {'TenantName': tenantName, 'DomainName': theDomainName,
                         'BenchmarkName': config['Schedule Discovery/Benchmark']}
                inputQueue.put(parameter)

        for i in range(1, maxThread):
            username =  ''.join([config['MultiThreadUsername'], f'{i:02}'])
            app = NetBrainIE(config['Url'], username, config['MultiThreadPassword'])
            if not app.Login():
                PrintMessage('Failed to login with the name: ' + username, 'Error')
                app = None
                continue
            apps.append(app)
            t = threading.Thread(target=StartWorkerThreadBenchmark, args=(app,))
            t.daemon = True
            t.start()

        # o = threading.Thread(target=OutputThread)
        # o.daemon = True
        # o.start()

        inputQueue.join()  # Block until all tasks are done
        # outputQueue.join()
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        for app in apps:
            if app.Logined:
                app.Logout()
        return ret
# Benchmark task end


def StartBTMSPBenchmark(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    GenerateTenant2TaskQueueBenchmark(config)
    GenerateTenant3to6TaskQueueBenchmark(config)
    GenerateTenant1TaskQueueBenchmark(config)
    #taskQueue = list(inputQueue.queue)
    StartBenchmarkMultiThread(config, '', '', inputQueue)
    # t1 = taskQueue[0]
    # t2 = taskQueue[1]
    # t3 = taskQueue[800]
    # t4 = taskQueue[1201]
    # t5 = taskQueue[1602]
    # t6 = taskQueue[2003]
    return True

if __name__ == "__main__":
    CreateDomain()
    #StartDiscovers()
    #StartMultiDomainDiscoverMultiThread()
    #StartDiscoverMultiThread()
    #StartDiscoverTenant1()
    #StartBTMSPDiscover()
    #StartBTMSPBenchmark()
    #DiscoverAmendment()
    pass

