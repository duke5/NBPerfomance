# Create by Tony Che at 2020-01

# Domain.py
# Feature description

import json
import queue
import threading
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\Domain31200.conf'
ConfigFile = r'.\conf\Domain31110.conf'
#ConfigFile = r'.\conf\Domain3197.conf'
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
            domainFrom = config.get('DomainName From', None)
            if domainFrom is None:
                domainCount = config.get('DomainCount', 1) + 1
                domainFrom = 1
                domainTo = domainCount
            else:
                domainTo = config.get('DomainName To', None)
                if domainTo is None:
                    domainTo = domainFrom + 1
                domainTo += 1
                domainCount = domainTo - domainFrom + 1
            telnetInfo = config.get('TelnetInfo', {})
            enablePasswdInfo = config.get('EnablePasswdInfo', {})
            snmpRoInfo = config.get('SnmpRoInfo', {})
            if domainCount > 2:
                for i in range(domainFrom, domainTo):
                    domainInfo = config['DomainInfo'].copy()
                    domainName = domainInfo['Domain Name']
                    domainInfo['Domain Name'] = f'{domainName}{i:02}'
                    ret = app.CreateDomainWithNetworkSetting(domainInfo, telnetInfo, enablePasswdInfo, snmpRoInfo)
                    app.ApplyTenantAndDomain(domainInfo['Tenant Name'], domainInfo['Domain Name'])
            else:
                ret = app.CreateDomainWithNetworkSetting(config['DomainInfo'], telnetInfo, enablePasswdInfo, snmpRoInfo)
                app.ApplyTenantAndDomain(config['DomainInfo']['Tenant Name'], config['DomainInfo']['Domain Name'])
    except Exception as e:
        print('Exception raised: ', str(e))
        return False
    finally:
        if application is None and logined:
            app.Logout()
        return True

def DeleteDomain(application=None, configFile=''):
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
            app.ApplyTenantAndDomain(config['DomainInfo']['Tenant Name'], config['DomainInfo']['Domain Name'])
        else:
            app = application
            logined = True
        if logined:
            domainInfo = config.get('DomainInfo', {})
            data = app._getUserInfoMainUI()
            tenants = data.get('tenant', [])
            domains = []
            for item in tenants:
                if item['name'] == domainInfo['Tenant Name']:
                    tenantID = item['ID']
                    domains = item['domains']
                    break
            if len(domains) <= 0:
                PrintMessage('There is no domain in the Tenant: ' + domainInfo['Tenant Name'], 'Error')
                ret = False
                return ret
            domainNames = list()
            for item in domains:
                domainNames.append(item['name'])
            domainFrom = int(config.get('DomainFrom', 1))
            domainTo = int(config.get('DomainTo', 1)) + 1
            domainCount = config.get('DomainCount', domainTo - domainFrom -1) + 1
            if domainCount > 2:
                for i in range(domainFrom, domainTo):
                    domainName = f'{domainInfo["Delete Domain Name"]}{i:04}'
                    if domainName in domainNames:
                        domain = domains[domainNames.index(domainName)]
                    else:
                        continue
                    deleteDomainInfo = {
                        'userGuid': app.UserID,
                        'companyGuid': tenantID,
                        'domainGuid': domain['guid'],
                        'dbName': domain['dbName']
                    }
                    PrintMessage('Delete domain: ' + domainName)
                    ret = app.DeleteDomain(deleteDomainInfo)
            else:
                domainName = domainInfo['Delete Domain Name']
                if domainName in domainNames:
                    domain = item[domainNames.index(domainName)]
                else:
                    PrintMessage('Failed to find the domain: ' + domainInfo['Domain Name'], 'Error')
                    ret = False
                    return ret
                deleteDomainInfo = {
                    'userGuid': app.UserID,
                    'companyGuid': tenantID,
                    'domainGuid': domain['guid'],
                    'dbName': domain['dbName']
                }
                PrintMessage('Delete domain: ' + domainName)
                ret = app.DeleteDomain(deleteDomainInfo)
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        return False
    finally:
        if application is None and logined:
            app.Logout()
        return True
    return


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
        print('Exception raised: ', str(e))
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
            domainFrom = config.get('DomainName From', None)
            if domainFrom is None:
                domainCount = config.get('DomainCount', 1) + 1
                domainFrom = 1
                domainTo = domainCount
            else:
                domainTo = config.get('DomainName To', None)
                if domainTo is None:
                    domainTo = domainFrom + 1
                domainTo += 1
                domainCount = domainTo - domainFrom + 1
            #count = config.get('DiscoverCount', 1) + 1
            if domainCount > 2:
                for index in range(domainFrom, domainTo):
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
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and logined:
            app.Logout()
        return ret


def WorkerThread(app, tenantName, domainName, discoverInfo, groupInfo={}):
    ret = app.ApplyTenantAndDomain(tenantName, domainName)
    if not ret:
        return ret
    if len(discoverInfo):
        discoverTaskID = app.StartDiscover(discoverInfo)
        if len(groupInfo):
            app.SaveDeviceGroup(groupInfo, discoverTaskID)

    return True

def WorkerThreadSingleTenant(app):
    while True:
        param = inputQueue.get()
        WorkerThread(app, param['TenantName'], param['DomainName'],
                     param['DiscoverInfo'], param['GroupInfo'])
        inputQueue.task_done()

    return True

def StartDiscoverMultiThread(configFile='', tenantName='', domainName=''):
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
            domainFrom = config.get('DomainName From', None)
            if domainFrom is None:
                domainCount = config.get('DomainCount', 1) + 1
                domainFrom = 1
                domainTo = domainCount
            else:
                domainTo = config.get('DomainName To', None)
                if domainTo is None:
                    domainTo = domainFrom + 1
                domainTo += 1
                domainCount = domainTo - domainFrom + 1
        maxThread = config.get('ThreadCount', 1) + 1
        # domainFrom = int(config.get('DomainFrom', 1))
        # domainTo = int(config.get('DomainTo', 1)) + 1
        apps = list()
        if maxThread <= 2:
            StartDiscover(None, config)
            return ret
        # Multi Thread
        for i in range(domainFrom, domainTo):
            #theDomainName = domainName  # ''.join([domainName, f'{i:04}'])
            theDomainName = ''.join([domainName, f'{i:02}'])
            discoverInfo = config.get('DiscoverInfoMulthThread', {})
            groupInfo = config.get('GroupInfoMulthThread', {}).copy()
            groupInfo['Name'] = ''.join([groupInfo['Name'], f'{i:02}'])
            parameter = {'TenantName': tenantName, 'DomainName': theDomainName,
                     'DiscoverInfo': discoverInfo, 'GroupInfo': groupInfo}
            inputQueue.put(parameter)

        for i in range(1, maxThread):
            username =  ''.join([config['MultiThreadUsername'], f'{i:02}'])
            app = NetBrainIE(config['Url'], username, config['MultiThreadPassword'])
            if not app.Login():
                PrintMessage('Failed to login with the name: ' + username, 'Error')
                app = None
            apps.append(app)
            t = threading.Thread(target=WorkerThreadSingleTenant, args=(app,))
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

def StartMultiDomainDiscoverMultiThread(configFile='', tenantName='', domainName=''):
    # not finished
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
                    break
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
        print('Exception raised: ', str(e))
        ret = False
    finally:
        for app in apps:
            app.Logout()
        return ret

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
            ips += '\n'.join([item['mgmtIP'], '\n'])
        with open(outFilename, 'w') as fp:  # r'c:\temp\fs167.txt'
            fp.write(lines)
            with open(outFilename+'.ip.csv', 'w') as fp:  # r'c:\temp\fs167.txt'
                fp.write(ips)
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    #CreateDomain()
    #StartDiscovers()
    #StartMultiDomainDiscoverMultiThread()
    StartDiscoverMultiThread()
    #DeleteDomain()
    #StartDiscover()
    #ExportIPinFS('', 'FS1', r'c:\temp\dev9898.csv')
