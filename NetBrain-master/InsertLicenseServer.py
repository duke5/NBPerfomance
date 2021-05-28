# Create by Tony Che at 2020-01

# InsertLicenseServer.py
# Feature description

import json
import os
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\InsertLicenseServer31200.conf'

def InsertLicenseServer(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False
    print('Insert License Server')

    webServer = config.get('WebServerAddress', '').replace('\\', '')
    licneseServerInfo = config.get('LicenseServerInfo', {})
    licenseServer = licneseServerInfo.get('Server', '10.10.10.40')
    licneseServerUsername = config.get('Username', None)  # licneseServerInfo.get('Username', None)
    licneseServerPassword = config.get('Password', None)  # licneseServerInfo.get('Password', None)
    licenseTrail = licneseServerInfo.get('Trail', '10.10.10.40')
    licenseSSL = licneseServerInfo.get('SSL', '0')
    licenseManagerFile = config.get('LicenseManagerFile', '').replace(':', '$')
    uncPath = ''.join([r'\\', webServer, '\\', licenseManagerFile])

    f = None
    ret = True
    try:
        if licneseServerUsername is not None:
            shareFolder = ''.join(['\\\\', webServer, '\\', licenseManagerFile[0], '$'])  # '\\192.168.31.200'\c$
            command = ''.join(['NET USE ', shareFolder, ' /USER:', licneseServerUsername, ' ', licneseServerPassword,
                               ' & NET USE ', shareFolder, ' DELETE'])
            with os.popen(command, 'r') as fp:
                result = fp.read().strip()
        f = open(uncPath, "r+")
        lines = f.readlines()
        if f'Server={licenseServer}\n' not in lines:
            newLines = list()
            for line in lines:
                newLines.append(line)
                if line.startswith('KeyInfo'):
                    newLines.append(f'Server={licenseServer}\nTrialServer={licenseTrail}\nSSL={licenseSSL}\n')
            f.seek(0)
            f.writelines(newLines)
            PrintMessage('InsertLicenseServer passed.')
    except IOError:
        PrintMessage('InsertLicenseServer failed: file io error.', 'Error')
        ret = False
    except Exception as e:
        PrintMessage(''.join(['InsertLicenseServer failed: ', str(e)]), 'Error')
        ret = False
    finally:
        if f is not None:
            f.close()
    print('Insert License Server Completed.')
    return ret


if __name__ == "__main__":
    InsertLicenseServer()

