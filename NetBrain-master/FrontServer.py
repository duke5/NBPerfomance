import json
import os
import re
import tempfile
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\FrontServer31200.conf'
FSConfigurationTemplate = [  # V8.02
    '[frontserver]',
    '# the unique id of fs',
    'fs.id=',     # 2
    '',
    '# the unique name of tenant',
    'tenant.name=',  # 5
    '',
    '# the authencation key of fs',
    'fs.authenticationkey=encrypted:',  # 8   mcO5GsvVtlIQurDItm85jiL1goomxTJ77RtGjaPdnck=
    'tenant.id=',  # 9
    'tenant.registed=1',
    '',
    '[fsc_conn]',
    '# the address of fsc',
    'addr=',  # 14
    '',
    '# the port of fsc',
    'port=',  # 17
    '',
    '# use ssl connect to fsc set 1, else 0',
    'ssl=',  # 20
    '',
    'ssl.verifyCert=0',
    'ssl.verifyCertFile=',
    'ssl.handshake.timeout=10',
    'reconn_sec=5',
    'disconn_sec=5',
    'ssl.cai=0',
    '[fsui]',
    'fsc_conn.addr=',  # 29
    'fsc_conn.port=',  # 30
    'fsc_conn.ssl=',   # 31
    'fsc_conn.ssl.verifyCert=0',
    'fsc_conn.ssl.cai=0',
    'frontserver.fs.id=',  # 34
    'frontserver.tenant.name=',  # 35
    'frontserver.fs.authenticationkey=encrypted:',  # 36   p52wmWBPVDddom2yVTg3Whcuyj9qHY26Or9Ckm6jCy0=
    'fsc_conn.ssl.verifyCertFile=',
    'fs.mult.host=',  # 38
    'frontserver.tenant.id=',  # 39
    '[PostgreSQL]',  # 40
    'pg.username=',  # 41
    'pg.password=encrypted:',  # 42
    'pg.port='
]
FSRegistrationTemplate = [  # V8.02
    '# Enter <hostname or IP address>:<port> of the Front Server Controller. For example, 192.168.1.1:9095',
    '# Use a semicolon to separate multiple Front Server Controllers.',
    'Front Server Controller =',     # 2
    '',
    '# Define the SSL settings. "no" indicates disable; "yes" indicates enable.',
    'Enable SSL = ',  # 5
    '',
    '# If enable conduct SSL certificate authority, please enter the full path of certificate file.',
    'Conduct SSL Certificate Authority = no',
    'SSL Certificate Path =',
    '',
    '# Define the Front Server register to',
    'Tenant Name =',  # 12
    'Front Server ID =']  # 13

def FrontServer():
    ret = True
    #NetBrainUtils.RunCommandOnRemoteServer2('cd /usr/lib/netbrain/frontserver/bin;./registration ', '192.168.31.186',
    #                                        'root', 'Netbrain1', 'Linux')
    #return ret
    AddFrontServer()
    #EditFrontServer()
    #DeleteFrontServer()
    #ini = LoadFrontServerConfiguration()
    #NetBrainUtils.SaveIniFile('c:\\temp\\test.ini', ini)
    #ret = RegisterFrontServer()
    if ret:
        return ret
        StartFrontServerService()

def AddFrontServer(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        print('Add Front Server')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            #app.CurrentVersion = '8.01'
            app.Login()
        else:
            app = application
        if app.Logined:
            '''
            fsCount = config.get('FSCount', 1) + 1
            if fsCount > 2:
                for i in range(1, fsCount):
                    fsInfo = config['FSInfo'].copy()
                    value = fsInfo['Front Server ID']
                    fsInfo['Front Server ID'] = f'{value}{i}'
                    ret = app.AddFrontServer(fsInfo)
            else:
                app.AddFrontServer(config['FSInfo'])
            '''
            current_config = config.copy()
            for fsInfo in config['FSInfo']:
                ret = app.AddFrontServer(fsInfo)
                if ret and config.get('FSCInfo', None) is not None:
                    current_config['FSInfo'].clear()
                    current_config['FSInfo'].append(fsInfo)
                    ret = RegisterFrontServer(app, current_config)
                if ret:
                    ret = True  # StartFrontServerService(fsInfo)
    except Exception as e:
        PrintMessage(''.join([CurrentMethodName(), ' Exception raised: ', str(e)]), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def EditFrontServer(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('Edit Front Server')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
        else:
            app = application
            logined = True
        if app.Logined:
            app.EditFrontServer('FS3', config['FSInfo'])
    except Exception as e:
        PrintMessage(''.join([CurrentMethodName(), ' Exception raised: ', str(e)]), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def DeleteFrontServer(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('Delete Front Server')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
        else:
            app = application
            logined = True
        if app.Logined:
            app.DeleteFrontServer(config['FSInfo']['Front Server ID'])
    except Exception as e:
        PrintMessage(''.join([CurrentMethodName(), ' Exception raised: ', str(e)]), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def LoadFrontServerConfiguration(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        content = []
        fsInfo = config['FSInfo']
        print('LoadFrontServerConfiguration')
        server = fsInfo['Front Server IP']
        operationSystem = fsInfo['Operation System']
        filename = fsInfo['Configuration Filename']
        if len(filename) <= 0:
            PrintMessage(''.join([CurrentMethodName(), ': please set Configuration File.']), 'Error')
            return False

        if operationSystem == 'Windows':
            fullname = ''.join(['\\\\', server, '\\', filename.replace(':', '$')])
            '''
            with open(fullname, 'r', newline='') as fp:
                content = fp.readlines()
            for line in content:
                print(line)
            '''
            configData = NetBrainUtils.LoadIniFile(fullname)
            #frontServer = configData.items('frontserver')
            #fscConn = configData.items('fsc_conn')
            #fsUI = configData.items('fsui')
        elif operationSystem == 'Linux':
            logined = True
        else:
            PrintMessage(''.join([CurrentMethodName(), ': the Operation System "', operationSystem,
                                  '" does NOT exist.']), 'Error')

    except Exception as e:
        PrintMessage(''.join([CurrentMethodName(), ' Exception raised: ', str(e)]), 'Error')
    finally:
        return configData

def GetEncryptedKey(fsInfo):
    operationSystem = fsInfo['Operation System']
    fsServer = fsInfo['Front Server IP']
    user = fsInfo['Username']
    pwd = fsInfo['Password']
    destFolder = fsInfo.get('Installation Path', '')
    encryptedKeys = {
        'fs': '',
        'pg': ''
    }
    encryptedKey = ''
    if operationSystem.lower() == 'windows':
        if destFolder.endswith('\\'):
            destFolder = destFolder[-1]
        tempdir = fsInfo['Encryption Folder']
        filename = os.path.join(tempdir, 'NBConfig-Enc-Dec.zip')
        destFilename = destFolder + '\\NBConfig-Enc-Dec.zip'
        NetBrainUtils.CopyFileToWindowsServer(fsServer, user, pwd, filename, destFilename)
        tempdir = tempfile.gettempdir()
        filename = os.path.join(tempdir, 'auth.bat')
        with open(filename,'w') as fp:
            command = ''.join(['cd "',destFolder, '\\NBConfig-Enc-Dec"\r\nNBConfigEncrypt ', fsInfo['Authentication Key'],
                               ' pwd\r\ntype pwd\r\ncd ..\r\nrmdir /s /q NBConfig-Enc-Dec\r\ndel NBConfig-Enc-Dec.zip'])
            fp.write(command)
        command = ''.join(['"', destFolder, r'\NBConfig-Enc-Dec\NBConfigEncrypt.exe" ',
                           fsInfo['Authentication Key'], ' pwd'])
        command = NetBrainUtils.RunCommandOnRemoteServer(command, fsServer, user, pwd)
        encryptedKey = re.search('[\w\W]*?cipher text: (.*)', command, re.I)
        encryptedKey = '' if encryptedKey is None else encryptedKey.groups()[0]
        encryptedKeys['fs'] = encryptedKey.replace('\n', '')
        if fsInfo['Authentication Key'] == fsInfo['Postgres']['password']:
            encryptedKeys['pg'] = encryptedKeys['fs']
        else:
            command = ''.join(['"', destFolder, r'\NBConfig-Enc-Dec\NBConfigEncrypt.exe" ',
                               fsInfo['Postgres']['password'], ' pwd'])
            command = NetBrainUtils.RunCommandOnRemoteServer(command, fsServer, user, pwd)
            encryptedKey = re.search('[\w\W]*?cipher text: (.*)', command, re.I)
            encryptedKey = '' if encryptedKey is None else encryptedKey.groups()[0]
            encryptedKeys['pg'] = encryptedKey.replace('\n', '')
        command = f'-c -v {filename}'
        NetBrainUtils.RunCommandOnRemoteServer(command, fsServer, user, pwd)
        if os.path.exists(filename):
            os.remove(filename)
    elif operationSystem.lower() == 'linux':
        NetBrainUtils.CopyFileToLinuxServer(fsServer, user, pwd, r'c:\tools\ssv.tar.gz', r'/var/tmp/ssv.tar.gz')
        command = ''.join(['cd /var/tmp/ssv;./NBInitSSV -enc ', fsInfo['Authentication Key']])
        encryptedKey = NetBrainUtils.RunCommandOnRemoteServer(command, fsServer, user, pwd, operationSystem)
        encryptedKeys['fs'] = encryptedKey.replace('\n', '')
        command = ''.join(['cd /var/tmp/ssv;./NBInitSSV -enc ', fsInfo['Postgres']['password'],
                           ';rm -rf /var/tmp/ssv;rm -rf ssv.tar.gz'])
        encryptedKey = NetBrainUtils.RunCommandOnRemoteServer(command, fsServer, user, pwd, operationSystem)
        encryptedKeys['pg'] = encryptedKey.replace('\n', '')
    print(encryptedKeys)
    return encryptedKeys

def GenerateConfigData(app, config):
    configData = FSConfigurationTemplate.copy()
    fsInfo = config['FSInfo']
    value = fsInfo['Front Server ID']
    configData[2] = ''.join([FSConfigurationTemplate[2], value])
    configData[34] = ''.join([FSConfigurationTemplate[34], value])
    tenantName = fsInfo['Tenant Name']
    tenantID = fsInfo.get('Tenant ID', None)
    if tenantID is None:
        tenantID, id = app.GetTenantDomainID(tenantName)
    configData[5] = ''.join([FSConfigurationTemplate[5], tenantName])
    configData[35] = ''.join([FSConfigurationTemplate[35], tenantName])
    configData[9] = ''.join([FSConfigurationTemplate[9], tenantID])
    configData[39] = ''.join([FSConfigurationTemplate[39], tenantID])
    value = GetEncryptedKey(fsInfo)  # fsInfo['Authentication Key Encrypted']
    configData[8] = ''.join([FSConfigurationTemplate[8], value['fs']])
    configData[36] = ''.join([FSConfigurationTemplate[36], value['fs']])
    configData[41] = ''.join([FSConfigurationTemplate[41], fsInfo['Postgres']['username']])
    configData[42] = ''.join([FSConfigurationTemplate[42], value['pg']])
    configData[43] = ''.join([FSConfigurationTemplate[43], fsInfo['Postgres']['port']])
    fscInfo = config.get('FSCInfo', None)
    if fscInfo is None:
        PrintMessage('GenerateConfigData: Failed to retrieve FSCInfo.', 'Error')
        return ''
    fscIP1 = fscInfo['FSCInfo'][0]['Hostname or IP Address']
    useSSL1 ='1' if fscInfo['useSSL'] else '0'
    port1 = fscInfo['FSCInfo'][0]['Port']
    configData[14] = ''.join([FSConfigurationTemplate[14], fscIP1])
    configData[17] = ''.join([FSConfigurationTemplate[17], port1])
    configData[20] = ''.join([FSConfigurationTemplate[20], useSSL1])
    if len(fscInfo['FSCInfo']) > 1:
        fscIP2 = fscInfo['FSCInfo'][1]['Hostname or IP Address']
        useSSL2 ='1' if fscInfo['useSSL'] else '0'
        port2 = fscInfo['FSCInfo'][1]['Port']
        configData[29] = ''.join([FSConfigurationTemplate[29], fscIP2])
        configData[30] = ''.join([FSConfigurationTemplate[30], port2])
        configData[31] = ''.join([FSConfigurationTemplate[31], useSSL2])
        configData[38] = ''.join([FSConfigurationTemplate[38], f'{fscIP1}:{port1};{fscIP2}:{port2}'])
        configData.insert(28, f'addr2={fscIP2}')
        configData.insert(29, f'port2={port2}')
    else:
        configData[29] = ''.join([FSConfigurationTemplate[29], fscIP1])
        configData[30] = ''.join([FSConfigurationTemplate[30], port1])
        configData[31] = ''.join([FSConfigurationTemplate[31], useSSL1])
        configData[38] = ''.join([FSConfigurationTemplate[38], f'{fscIP1}:{port1}'])
    if fsInfo['Operation System'] == 'Windows':
        configData = '\r\n'.join([line for line in configData])
    else:
        configData = '\n'.join([line for line in configData])

    return configData.encode('utf-8')

def GenerateRegistrationData(config):
    configData = FSRegistrationTemplate.copy()
    fscInfo = config.get('FSCInfo', None)
    if fscInfo is None:
        PrintMessage('GenerateConfigData: Failed to retrieve FSCInfo.', 'Error')
        return ''
    fscIP = fscInfo[0]['Hostname or IP Address']
    port = fscInfo[0]['Port']
    configData[2] += f'{fscIP}:{port}'
    configData[5] += 'yes' if fscInfo[0]['useSSL'] else 'no'
    if len(fscInfo) > 1:
        fscIP = fscInfo[1]['Hostname or IP Address']
        port = fscInfo[1]['Port']
        configData[2] += f';{fscIP}:{port}'
    configData[12] += config['FSInfo']['Tenant Name']
    configData[13] += config['FSInfo']['Front Server ID']

    configData = '\n'.join([line for line in configData])

    return configData.encode('utf-8')

def UpdateDatabase(fsInfo, dbInfo):
    fsServer = fsInfo['Front Server IP']
    fsID = fsInfo['Front Server ID']
    hostname = fsInfo['Hostname']
    appDB = NetBrainDB(dbInfo)
    if appDB.Login():
        dbNGSystem = appDB.GetDatabase('NGSystem')
        tableFS = dbNGSystem['FrontServerAndGroup']
        condition = {'_id': fsID}
        fsData = tableFS.find_one(condition)
        if len(fsData) <= 0:
            PrintMessage(''.join([CurrentMethodName(), ': Failed to find FS "', fsID, '" in DB.']), 'Error')
            return False
        fsData['alias'] = hostname
        fsData['ipOrHostname'] = fsServer
        fsData['registered'] = True
        fsData['tsRegistered'] = NetBrainUtils.DateTimeToString(NetBrainUtils.GetUtcTime(), 2)
        field = fsData.get('operateInfo', None)
        if field is not None:
            del fsData['operateInfo']
        field = fsData.get('fsIds', None)
        if field is not None:
            del fsData['fsIds']
        content = appDB.Update('FrontServerAndGroup', condition, fsData)
        ret = True if 'ok' in content else False
        return ret

def RegisterFrontServer(application=None, configFile='', configData=None):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    try:
        ret = True
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
        else:
            app = application
        print(CurrentMethodName())
        for fsInfo in config['FSInfo']:
            destFolder = fsInfo.get('Installation Path', '')
            if len(destFolder) <= 0:
                PrintMessage(''.join([CurrentMethodName(), ': please set Installation Path.']), 'Error')
                return False
            # fsInfo['Encryption Folder'] = config['Encryption Folder']
            fsServer = fsInfo['Front Server IP']
            operationSystem = fsInfo['Operation System']
            user = fsInfo['Username']
            pwd = fsInfo['Password']
            if operationSystem == 'Windows':
                content = GenerateConfigData(app, {"FSInfo": fsInfo, "FSCInfo": config['FSCInfo']})
                if len(content) <= 0:
                    PrintMessage(''.join([CurrentMethodName(), ': failed to generate config data.']), 'Error')
                    break
                tempFilename = os.path.join(tempfile.gettempdir(), 'frontserver.ini')
                #print(tempFilename)
                with open(tempFilename, 'wb') as fp:
                    fp.write(content)
                StopFrontServerService(fsInfo)
                filename = os.path.join(destFolder, r'conf\frontserver.ini')
                content = NetBrainUtils.CopyFileToWindowsServer(fsServer, user, pwd, tempFilename, filename)
                if not content:
                    PrintMessage('Failed to copy config file to windows server: ' + content, 'Error')
                    ret = False
                filename = os.path.join(destFolder, r'bin\frontserver.exe')
                content = ''.join(['"', filename, '" -regist'])
                content = NetBrainUtils.RunCommandOnRemoteServer(content, fsServer, user, pwd)
                fsServer = re.search('[\w\W*?(STATE\s*:\s*4\s*RUNNING).*]', content, re.I)
                if fsServer is None:
                    PrintMessage(content, 'Error')
                StartFrontServerService(fsInfo)
            elif operationSystem == 'Linux':
                content = GenerateRegistrationData({"FSInfo": fsInfo, "FSCInfo": config['FSCInfo']})
                if len(content) <= 0:
                    PrintMessage(''.join([CurrentMethodName(), ': failed to generate config data.']), 'Error')
                    ret = False
                tempFilename = os.path.join(tempfile.gettempdir(), 'register_frontserver.conf')
                #print(tempFilename)
                with open(tempFilename, 'wb') as fp:
                    fp.write(content)
                if not destFolder.endswith('/'):
                    destFolder += '/'
                filename = f'{destFolder}conf/register_frontserver.conf'
                content = NetBrainUtils.CopyFileToLinuxServer(fsServer, user, pwd, tempFilename, filename)
                if not content:
                    PrintMessage('Failed to copy config file to linux server', 'Error')
                    ret = False
                filename = destFolder + r'bin'
                #content = ''.join(['cd ', filename, ';./frontserver -regist;service netbrainfrontserver start;',
                #                   'service netbrainfrontserver status'])
                content = ''.join(['cd ', destFolder, 'bin;./registration '])
                content = NetBrainUtils.RunCommandOnRemoteServer(content, fsServer, user, pwd, 'Linux', ['netbrain'])
                fsServer = re.search('[\w\W]*?(Successfully updated the registration).*', content, re.I)
                if fsServer is None:
                    PrintMessage(''.join(['Failed to register Front Server: ', fsInfo['Front Server ID']]), 'Error')
                    print(content)
                StartFrontServerService(fsInfo)
            else:
                PrintMessage(''.join([CurrentMethodName(), ': the Operation System "', operationSystem,
                                      '" does NOT exist.']), 'Error')
            os.remove(tempFilename) if os.path.exists(tempFilename) else None

    except Exception as e:
        PrintMessage(''.join([CurrentMethodName(), ' Exception raised: ', str(e)]), 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def GetWindowsServiceStatus(fsInfo, serviceName):
    fsServer = fsInfo['Front Server IP']
    user = fsInfo['Username']
    pwd = fsInfo['Password']
    result = NetBrainUtils.RunCommandOnRemoteServer(''.join(['sc query "', serviceName, '"']), fsServer, user, pwd)
    #print(result)
    status = re.search('[\w\W]*?STATE\s*:\s*(\d+)\s*(\w*)\s*', result, re.I)
    if status is not None:
        status = status.groups()
    print('======>', status)
    if status is None or len(status) != 2:
        status = ('Error', 'Failed to run command on remote server.')
    return status

def GetLinuxServiceStatus(remoteServer, username, password, serviceName):
    result = NetBrainUtils.RunCommandOnRemoteServer(''.join(['service ', serviceName, ' status']),
                                                    remoteServer, username, password, 'Linux')
    print(result)
    status = re.search('[\w\W]*?active\s*:\s*(\w+)\s*\((.*?)\)\s*', result.lower(), re.I).groups()
    print('======>', status)
    if status is None or len(status) != 2:
        status = ('Error', 'Failed to run command on remote server.')
    return status

def StartFrontServerService(fsInfo):
    if len(fsInfo) <= 0:
        PrintMessage('Failed to load the FS configuration: ', 'Error')
        return False
    try:
        ret = True
        print(CurrentMethodName())
        fsServer = fsInfo['Front Server IP']
        user = fsInfo['Username']
        pwd = fsInfo['Password']
        operationSystem = fsInfo['Operation System']
        if operationSystem == 'Windows':
            status = GetWindowsServiceStatus(fsInfo, 'NetBrainFrontServer')
            if status[0] == '4':
                cmd = 'sc stop "NetBrainFrontServer"'
                result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd)
                print(result)
            cmd = 'sc start "NetBrainFrontServer"'
            result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd)
            #print(result)
            status = GetWindowsServiceStatus(fsInfo, 'NetBrainFrontServer')
            if status[0] != '4':
                PrintMessage(''.join(['Servie status is ', status[1], '(', status[0], ').']), 'Error')
                ret = False
        elif operationSystem == 'Linux':
            user = fsInfo['Username']
            pwd = fsInfo['Password']
            status = GetLinuxServiceStatus(fsServer, user, pwd, 'netbrainfrontserver')
            if status[0] == 'active':
                cmd = 'service netbrainfrontserver stop'
                result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd, 'Linux')
                print(result)
            cmd = 'service netbrainfrontserver start'
            result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd, 'Linux')
            #print(result)
            status = GetLinuxServiceStatus(fsServer, fsInfo['Username'], fsInfo['Password'],
                                           'netbrainfrontserver')
            if status[0] != 'active':
                PrintMessage(''.join(['Servie status is ', status[1], '(', status[0], ').']), 'Error')
                ret = False
        else:
            PrintMessage(''.join([CurrentMethodName(), ': the Operation System "', operationSystem,
                                  '" does NOT exist.']), 'Error')

    except Exception as e:
        PrintMessage(''.join([CurrentMethodName(), ' Exception raised: ', str(e)]), 'Error')
        ret = False
    finally:
        return ret

def StopFrontServerService(fsInfo):
    if len(fsInfo) <= 0:
        PrintMessage('Failed to load the FS configuration: ', 'Error')
        return False
    try:
        ret = True
        print(CurrentMethodName())
        fsServer = fsInfo['Front Server IP']
        user = fsInfo['Username']
        pwd = fsInfo['Password']
        operationSystem = fsInfo['Operation System']
        if operationSystem == 'Windows':
            cmd = 'sc stop "NetBrainFrontServer"'
            result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd)
            status = GetWindowsServiceStatus(fsInfo, 'NetBrainFrontServer')
            if status[0] != '1':
                PrintMessage(''.join(['Servie status is ', status[1], '(', status[0], ').']), 'Error')
                print(result)
                ret = False
        elif operationSystem == 'Linux':
            user = fsInfo['Username']
            pwd = fsInfo['Password']
            cmd = 'service netbrainfrontserver stop'
            result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd, 'Linux')
            status = GetLinuxServiceStatus(fsServer, fsInfo['Username'], fsInfo['Password'], 'netbrainfrontserver')
            if status[0] != 'failed':
                PrintMessage(''.join(['Servie status is ', status[1], '(', status[0], ').']), 'Error')
                print(result)
                ret = False
        else:
            PrintMessage(''.join([CurrentMethodName(), ': the Operation System "', operationSystem,
                                  '" does NOT exist.']), 'Error')

    except Exception as e:
        PrintMessage(''.join([CurrentMethodName(), ' Exception raised: ', str(e)]), 'Error')
        ret = False
    finally:
        return ret

def StartPostgreSQLService(fsInfo):
    if len(fsInfo) <= 0:
        PrintMessage('Failed to load the FS configuration: ', 'Error')
        return False
    try:
        ret = True
        print(CurrentMethodName())
        fsServer = fsInfo['Front Server IP']
        user = fsInfo['Username']
        pwd = fsInfo['Password']
        operationSystem = fsInfo['Operation System']
        if operationSystem == 'Windows':
            status = GetWindowsServiceStatus(fsInfo, 'NetBrainFrontServer')
            if status[0] == '4':
                cmd = 'net stop "PostgreSQL"'
                result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd)
                print(result)
            cmd = 'net start "PostgreSQL"'
            result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd)
            #print(result)
            status = GetWindowsServiceStatus(fsInfo, 'PostgreSQL')
            if status[0] != '4':
                PrintMessage(''.join(['Servie status is ', status[1], '(', status[0], ').']), 'Error')
                ret = False
        elif operationSystem == 'Linux':
            user = fsInfo['Username']
            pwd = fsInfo['Password']
            status = GetLinuxServiceStatus(fsServer, user, pwd, 'postgresql')
            if status[0] == 'active':
                cmd = 'service postgresql stop'
                result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd, 'Linux')
                print(result)
            cmd = 'service postgresql start'
            result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd, 'Linux')
            #print(result)
            status = GetLinuxServiceStatus(fsServer, fsInfo['Username'], fsInfo['Password'], 'postgresql')
            if status[0] != 'active':
                PrintMessage(''.join(['Servie status is ', status[1], '(', status[0], ').']), 'Error')
                ret = False
        else:
            PrintMessage(''.join([CurrentMethodName(), ': the Operation System "', operationSystem,
                                  '" does NOT exist.']), 'Error')

    except Exception as e:
        PrintMessage(''.join([CurrentMethodName(), ' Exception raised: ', str(e)]), 'Error')
        ret = False
    finally:
        return ret

def StopPostgreSQLService(fsInfo):
    if len(fsInfo) <= 0:
        PrintMessage('Failed to load the FS configuration: ', 'Error')
        return False
    try:
        ret = True
        print(CurrentMethodName())
        fsServer = fsInfo['Front Server IP']
        user = fsInfo['Username']
        pwd = fsInfo['Password']
        operationSystem = fsInfo['Operation System']
        if operationSystem == 'Windows':
            cmd = 'net stop "PostgreSQL"'
            result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd)
            status = GetWindowsServiceStatus(fsInfo, 'PostgreSQL')
            if status[0] != '1':
                PrintMessage(''.join(['Servie status is ', status[1], '(', status[0], ').']), 'Error')
                print(result)
                ret = False
        elif operationSystem == 'Linux':
            user = fsInfo['Username']
            pwd = fsInfo['Password']
            cmd = 'service postgresql stop'
            result = NetBrainUtils.RunCommandOnRemoteServer(cmd, fsServer, user, pwd, 'Linux')
            status = GetLinuxServiceStatus(fsServer, fsInfo['Username'], fsInfo['Password'], 'postgresql')
            if status[0] != 'failed':
                PrintMessage(''.join(['Servie status is ', status[1], '(', status[0], ').']), 'Error')
                print(result)
                ret = False
        else:
            PrintMessage(''.join([CurrentMethodName(), ': the Operation System "', operationSystem,
                                  '" does NOT exist.']), 'Error')

    except Exception as e:
        PrintMessage(''.join([CurrentMethodName(), ' Exception raised: ', str(e)]), 'Error')
        ret = False
    finally:
        return ret


if __name__ == '__main__':
    FrontServer()
