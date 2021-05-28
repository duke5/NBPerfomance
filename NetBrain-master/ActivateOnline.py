# Create by Tony Che at 2020-01

# ActivateOnline.py
# Feature description

import traceback
import time
import InsertLicenseServer
import FrontServer
import FrontServerController
import SkipKCVerification
import User
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid
import Domain
import ScheduleTask
from EnableGoldenBaselineDynamicCalculation import EnableGoldenBaselineDynamicCalculation

ConfigFile = r'.\conf\ActivateOnline31200.conf'
#ConfigFile = r'.\conf\ActivateOnline30198.conf'
#ConfigFile = r'.\conf\ActivateOnline9898.conf'
ConfigFile = r'.\conf\ActivateOnline3197.conf'
ConfigFile = r'.\conf\ActivateOnline31110.conf'

def ActivateOnline(configFile=''):
    #content = NetBrainUtils.ReadFileFromRemoteServer('192.168.31.97', 'administrator', 'Netbrain1', 'c:\\temp\\test.ini')
    #content2 = NetBrainUtils.ReadFileFromRemoteServer('192.168.31.95', 'root', 'Netbrain1', '/opt/input', 'Linux')
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        app = NetBrainIE(config['Url'], config['Username'])
        activateInfo = config['ActivateInfo']
        #if app.CurrentVersion <= 8.03:
        ret = InsertLicenseServer.InsertLicenseServer(activateInfo['InsertLicenseServerInfo'])
        if not ret:
            return False
        # version = app.GetVersion()
        # app.SetVersion(config['Version'])
        #print('ActivateOnline')
        ret = app.ActivateOnline(activateInfo['New Password'], activateInfo['UserInfo'], activateInfo['LicenseInfo'],
                  activateInfo['TenantInfo'], activateInfo['EmailSetting'], 'admin', activateInfo['Old Password'])
        #ret = True
        if ret:
            config['Password'] = config['ActivateInfo']['New Password']
            AllowPostgresRemoteConnection(config)
            ret = AddFSCandFS(config)
            AddUsers(config)
            skipKCVerificationInfo = config.get('SkipKCVerificationInfo', {})
            #SkipKCVerification.SkipKCVerification(skipKCVerificationInfo)
            SkipKCVerification.SkipKCVerification2(skipKCVerificationInfo)

    except Exception as e:
        traceback.print_exc()
        # print('Exception raised: ', str(e))
        ret = False
    finally:
        if app is not None and app.Logined:
            app.Logout()
        return ret

def AllowPostgresRemoteConnection(config):
    for fs in config['FSInfo']:
        restart_service = False
        if fs['Operation System'].lower() == 'windows':
            server = fs['Front Server IP']
            install_path = fs['Installation Path']
            index = install_path.rfind('\\')
            postgres_folder = ''.join(['\\\\', server, '\\', install_path[:index].replace(':', '$'), '\\PostgresData\\'])
            restart_service = False
            with open(postgres_folder + 'pg_hba.conf', 'r+') as fp:
                fp.seek(0)
                content = fp.read()
                config = 'host    all             all             0.0.0.0/0	            scram-sha-256\n'
                if config not in content:
                    content += config
                    fp.seek(0)
                    fp.write(content)
                    restart_service = True
            with open(postgres_folder + 'postgresql.conf', 'r+') as fp:
                fp.seek(0)
                content = fp.read()
                config = "listen_addresses = '*'"
                if config not in content:
                    content += "listen_addresses = '*'\n"
                    #content.replace('listen_addresses = \'127.0.0.1\'', 'listen_addresses = \'*\'')
                    content = content.replace("listen_addresses = '127.0.0.1'", "# listen_addresses = '127.0.0.1'")
                    fp.seek(0)
                    fp.write(content)
                    restart_service = True
        else:
            PrintMessage(f'Linux FS ({fs["Front Server ID"]}) have not been supported yet.', 'Error')
        if restart_service:
            FrontServer.StopPostgreSQLService(fs)
            FrontServer.StartPostgreSQLService(fs)
    return True

def AddFSCandFS(config):
    ret = FrontServerController.AddFrontServerController(None, config)
    if ret:
        ret = FrontServer.AddFrontServer(None, config)
    return ret


def AddUsers(config):
    ret = User.AddUser(None, config)
    return ret

def CreateDomainAndDiscover(application, config):
    if type(config) is str:
        config = NetBrainUtils.GetConfig(config)
    if len(config) == 0:
        PrintMessage('no config is loaded.', 'Error')
        return False

    try:
        ret = True
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'])
        else:
            app = application
        if not app.Logined:
            app.Login(config['Username'], config['ActivateInfo']['New Password'])
        Domain.CreateDomain(app, config['New Domain Info'])
        telnetInfo = config['New Domain Info'].get('TelnetInfo1', {})
        enablePasswdInfo = config['New Domain Info'].get('EnablePasswdInfo1', {})
        snmpRoInfo = config['New Domain Info'].get('SnmpRoInfo1', {})
        app.UpdateTelnetInfo(telnetInfo)
        app.UpdateEnablePasswd(enablePasswdInfo)
        app.UpdateSnmpRoInfo(snmpRoInfo)
        Domain.StartDiscover(app, config['New Domain Info'])

    except Exception as e:
        traceback.print_exc()
        # print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def SetGlobalDataCleanSettings(app:NetBrainIE, config):
    option = config.get('Global Data Clean Settings', {}).get('Data Engine Data', None)
    if option is None:
        ret = True
    else:
        ret = app.setDataCleanOption(option)
    option = config.get('Global Data Clean Settings', {}).get('Other Data', None)
    if option is not None:
        app.DataCleanOption(option)
    return ret

if __name__ == "__main__":
    config = NetBrainUtils.GetConfig(ConfigFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', ConfigFile]), 'Error')
        exit(1)

    try:
        app = None
        ret = ActivateOnline(config)
        if not ret:
            PrintMessage('Activate failed.', 'Error')
            exit(1)
        config['Password'] = config['ActivateInfo']['New Password']
        app = NetBrainIE(config['Url'], config['Username'], config['Password'])
        app.Login()
        if app.Logined:
            app.EnableAutoUpdate(False)
            CreateDomainAndDiscover(app, config)
            config['Tenant Name'] = config['New Domain Info']['DomainInfo']['Tenant Name']
            config['Domain Name'] = config['New Domain Info']['DomainInfo']['Domain Name']
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
            # EnableGoldenBaselineDynamicCalculation(config)  # call it after the domain is created
            ScheduleTask.SaveScheduleBenchmark(app, config)
            SetGlobalDataCleanSettings(app, config)
            ScheduleTask.StartScheduleTasks(app, config)

    except Exception as e:
        # traceback.print_exc()
        exception_stack = traceback.format_exc()
        PrintMessage('Exception raised: ' + exception_stack, 'Error')
        ret = False

    finally:
        #logger.close()
        if app is not None and app.Logined:
            app.Logout()
